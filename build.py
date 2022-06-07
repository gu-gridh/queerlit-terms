from datetime import datetime
from itertools import filterfalse
import os
from os.path import join
import re
from dotenv import load_dotenv
from rdflib import DCTERMS, SKOS, XSD, Literal
from qlit.identifier import generate_identifier, validate_identifier
from qlit.simple import name_to_ref, ref_to_name
from qlit.thesaurus import Termset, Thesaurus

load_dotenv()

THESAURUSFILE = os.environ.get('THESAURUSFILE')
if not THESAURUSFILE:
    raise EnvironmentError('Error: THESAURUSFILE missing from env')

INDIR = os.environ.get('INDIR')
if not INDIR:
    raise EnvironmentError('Error: INDIR missing from env')

rdf_now = Literal(
    datetime.utcnow().isoformat().split('.')[0],
    datatype=XSD.dateTime)


def randomize_ids(thesaurus: Thesaurus):
    """Replace all non-randomized ids with new, randomized ids."""
    uris = thesaurus.refs()
    ids = [thesaurus.value(uri, DCTERMS.identifier) for uri in uris]
    bad_ids = filterfalse(validate_identifier, ids)
    for bad_id in bad_ids:
        new_id = generate_identifier(ids)
        print(f'New id {new_id} for {bad_id}')
        replace_identifier(thesaurus, bad_id, new_id)

def replace_identifier(thesaurus: Thesaurus, old_id: str, new_id: str):
    """Replace all statements about the term `old_id` with statements about `new_id`"""
    old_ref = name_to_ref(old_id)
    new_ref = name_to_ref(new_id)
    # Update outgoing statements
    for p, o in thesaurus.predicate_objects(old_ref):
        thesaurus.remove((old_ref, p, o))
        thesaurus.add((new_ref, p, o))
    # Update incoming relations
    for s, p in thesaurus.subject_predicates(old_ref):
        thesaurus.remove((s, p, old_ref))
        thesaurus.add((s, p, new_ref))
    # Update identifier literal
    thesaurus.set((new_ref, DCTERMS.identifier, Literal(new_id)))


def check_changes(thesaurus: Thesaurus, thesaurus_prev: Thesaurus):
    ps = [SKOS.altLabel, SKOS.broader, SKOS.broadMatch, SKOS.exactMatch, SKOS.narrower, SKOS.prefLabel, SKOS.scopeNote]
    
    uris = thesaurus.refs()
    uris_prev = thesaurus_prev.refs()
    
    count_new = 0
    count_changed = 0
    count_removed = len(list(uri for uri in uris_prev if uri not in uris))

    for term_uri in uris:
        if term_uri not in uris_prev:
            # This term is a new addition.
            thesaurus.set((term_uri, DCTERMS.issued, rdf_now))
            thesaurus.set((term_uri, DCTERMS.modified, rdf_now))
            count_new += 1
        else:
            # Are there any changes in the term?
            changed_ps = []
            for p in ps:
                a = sorted(thesaurus.objects(term_uri, p))
                b = sorted(thesaurus_prev.objects(term_uri, p))
                if a != b:
                    changed_ps.append(p)
                    # print(p)
                    # print(a)
                    # print(b)
            if (changed_ps):
                # The term has changes.
                p_names = [re.sub(r'.*[/#]', '', p) for p in changed_ps]
                print(f'Changes for {ref_to_name(term_uri)} in {", ".join(p_names)}')
                thesaurus.set((term_uri, DCTERMS.modified, rdf_now))
                count_changed += 1
    return count_changed, count_new, count_removed


if __name__ == '__main__':
    # Load current state.
    thesaurus = Thesaurus()

    # Prepare parsing.
    fns = [fn for fn in os.listdir(INDIR) if not fn.startswith('.')]
    print(f'Parsing {len(fns)} files...')
    skipped = []

    # Parse input files.
    for fn in fns:
        try:
            with open(join(INDIR, fn)) as f:
                data = f.read()
            termset = Termset().parse(data=data)
            # Catch common syntax mistake
            for s, p, o in termset:
                if p.endswith(':'):
                    raise SyntaxError(f'Predicate ends with colon: {p}')
            term_uri = termset.refs()[0]
            thesaurus.remove((term_uri, None, None))
            thesaurus += termset
        except Exception as err:
            # Report error and skip this input file.
            print(f'{fn}: {type(err)} {err}')
            skipped.append(fn)

    # Done parsing.
    if skipped:
        print(f'WARNING: Skipped {len(skipped)} files')
    print(f'Parsed {len(fns) - len(skipped)} files')

    # Randomize new ids
    print('Creating new identifiers...')
    randomize_ids(thesaurus)

    # Complete relations
    print('Completing relations...')
    thesaurus.complete_relations()

    # Load another copy to track changes.
    print('Checking changes...')
    thesaurus_prev = Thesaurus().parse(THESAURUSFILE)
    count_changed, count_new, count_removed = check_changes(thesaurus, thesaurus_prev)
    print(f'{count_changed} changed, {count_new} new, {count_removed} removed')

    # Write result.
    terms = thesaurus.refs()
    print(f'Writing {len(terms)} terms...')
    thesaurus.base = None
    nt_data = thesaurus.serialize(format='nt')
    nt_lines = sorted(nt_data.splitlines(True))
    with open(THESAURUSFILE, 'w') as f:
        f.writelines(nt_lines)
    print(f'Wrote {THESAURUSFILE}')

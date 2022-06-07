from datetime import datetime
from itertools import filterfalse
import os
from os.path import join
import sys
from dotenv import load_dotenv
from rdflib import DCTERMS, SKOS, XSD, Literal, URIRef
from qlit.identifier import generate_identifier, validate_identifier
from qlit.simple import name_to_ref, ref_to_name
from qlit.thesaurus import BASE, Termset, Thesaurus

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



def update_or_create_term(thesaurus: Thesaurus, termset: Termset):
    # TODO: Update modified in complete_relations() too
    term_uri = termset.refs()[0]
    identifier = termset.value(term_uri, DCTERMS.identifier)
    termset.base = BASE
    
    existing_terms = list(thesaurus.subjects(DCTERMS.identifier, identifier))
    if len(existing_terms) > 1:
        raise ValueError(f'Multiple terms with id "{identifier}"')
    if existing_terms:
        update_term(thesaurus, termset)
    else:
        print(f'Adding new term {identifier}')
        termset.set((term_uri, DCTERMS.issued, rdf_now))
        termset.set((term_uri, DCTERMS.modified, rdf_now))
        thesaurus += termset

def update_term(thesaurus: Thesaurus, termset: Termset):
    term_uri = termset.refs()[0]
    old_termset = thesaurus.terms_if(lambda term: term == term_uri)
    # ps = [SKOS.altLabel, SKOS.broader, SKOS.broadMatch, SKOS.exactMatch, SKOS.narrower, SKOS.prefLabel, SKOS.scopeNote]
    ps = [SKOS.altLabel, SKOS.broadMatch, SKOS.exactMatch, SKOS.prefLabel, SKOS.scopeNote]
    has_changed = False
    for p in ps:
        if list(termset.objects(term_uri, p)) != list(old_termset.objects(term_uri, p)):
            if not has_changed:
                print(f'Updating term {ref_to_name(term_uri)}')
            print(f'- Change in {p}')
            thesaurus.remove((term_uri, p, None))
            thesaurus += termset.triples((term_uri, p, None))
            thesaurus.set((term_uri, DCTERMS.modified, rdf_now))
            has_changed = True
    return has_changed

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



if __name__ == '__main__':
    # Load current state.
    thesaurus = Thesaurus().parse(THESAURUSFILE)

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
            update_or_create_term(thesaurus, termset)
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

    # Write result.
    terms = thesaurus.refs()
    print(f'Writing {len(terms)} terms...')
    thesaurus.base = None
    nt_data = thesaurus.serialize(format='nt')
    nt_lines = sorted(nt_data.splitlines(True))
    with open(THESAURUSFILE, 'w') as f:
        f.writelines(nt_lines)
    print(f'Wrote {THESAURUSFILE}')

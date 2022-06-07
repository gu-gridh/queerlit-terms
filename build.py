from datetime import datetime
import os
from os.path import join
import sys
from dotenv import load_dotenv
from rdflib import DCTERMS, SKOS, XSD, Literal, URIRef
from qlit.identifier import generate_identifier, validate_identifier
from qlit.simple import name_to_ref
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



def update_term(thesaurus: Thesaurus, termset: Termset):
    # TODO: Don't randomize new ids until after parsing all ttls (they are in values too)
    # TODO: Update modified in complete_relations() too
    term_uri = termset.refs()[0]
    identifier = termset.value(term_uri, DCTERMS.identifier)
    termset.base = BASE
    
    existing_terms = list(thesaurus.subjects(DCTERMS.identifier, identifier))
    if len(existing_terms) > 1:
        raise ValueError(f'Multiple terms with id "{identifier}"')
    if existing_terms:
        if has_term_changed(thesaurus, termset):
            print(f'Updating term {identifier}')
            thesaurus.remove((term_uri, None, None))
            thesaurus += termset
            termset.set((term_uri, DCTERMS.modified, rdf_now))
    else:
        print(f'Adding new term {identifier}')
        termset.set((term_uri, DCTERMS.issued, rdf_now))
        termset.set((term_uri, DCTERMS.modified, rdf_now))
        if not validate_identifier(identifier):
            old_identifier = identifier
            identifier = generate_identifier()
            print(f'- Replacing id {old_identifier} with {identifier}')
            replace_identifier(termset, old_identifier, identifier)
        thesaurus += termset

def replace_identifier(termset: Termset, old: str, new: str):
    old_uri = name_to_ref(old)
    new_uri = name_to_ref(new)
    for p, o in termset.predicate_objects(old_uri):
        if p == DCTERMS.identifier:
            termset.add((new_uri, p, Literal(new)))
        else:
            termset.add((new_uri, p, o))
    termset.remove((old_uri, None, None))

def has_term_changed(thesaurus: Thesaurus, termset: Termset):
    term_uri = termset.refs()[0]
    old_termset = thesaurus.terms_if(lambda term: term == term_uri)
    ps = [SKOS.altLabel, SKOS.broader, SKOS.broadMatch, SKOS.exactMatch, SKOS.narrower, SKOS.prefLabel, SKOS.scopeNote]
    has_changed = False
    for p in ps:
        if list(termset.objects(term_uri, p)) != list(old_termset.objects(term_uri, p)):
            print(f'- Change in {p}')
            has_changed = True
    return has_changed

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
            update_term(thesaurus, termset)
        except Exception as err:
            # Report error and skip this input file.
            print(f'{fn}: {type(err)} {err}')
            skipped.append(fn)

    # Done parsing.
    if skipped:
        print(f'WARNING: Skipped {len(skipped)} files')
    print(f'Parsed {len(fns) - len(skipped)} files')

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

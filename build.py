from os import listdir
import os
from os.path import join
from dotenv import load_dotenv
from rdflib import Graph
from qlit.thesaurus import Thesaurus

load_dotenv()

if __name__ == '__main__':
    if 'INDIR' not in os.environ:
        raise EnvironmentError('Error: INDIR missing from env')

    # Prepare parsing.
    fns = [fn for fn in listdir(os.environ['INDIR']) if not fn.startswith('.')]
    print(f'Parsing {len(fns)} files...')
    thesaurus = Thesaurus()
    skipped = []

    # Parse input files.
    for fn in fns:
        # Skip non-RDF files.
        if fn.startswith('.'):
            continue

        try:
            with open(join(os.environ['INDIR'], fn)) as f:
                data = f.read()
                data = data.replace('http://queerlit.se/qlit/',
                                    'https://queerlit.dh.gu.se/qlit/v1/')
                data = data.replace('http://queerlit.se/termer',
                                    'https://queerlit.dh.gu.se/qlit/v1')
            term_graph = Graph().parse(data=data)
            for s, p, o in term_graph:
                if p.endswith(':'):
                    raise Exception(f'Predicate ends with colon: {p}')
            thesaurus += term_graph
        except Exception as err:
            # Report error and skip this input file.
            print(f'{fn}: {type(err)} {err}')
            skipped.append(fn)

    # Done parsing.
    if skipped:
        print(f'WARNING: Skipped {len(skipped)} files')
    print(f'Parsed {len(fns) - len(skipped)} files')

    # Complete relations
    thesaurus.complete_relations()

    # Write result.
    terms = thesaurus.refs()
    OUTFILE = 'qlit.nt'
    print(f'Writing {len(terms)} terms...')
    thesaurus.base = None
    nt_data = thesaurus.serialize(format='nt')
    nt_lines = sorted(nt_data.splitlines(True))
    with open(OUTFILE, 'w') as f:
        f.writelines(nt_lines)
    print(f'Wrote {OUTFILE}')

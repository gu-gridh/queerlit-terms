

from os import listdir
from os.path import join

from rdflib import Graph
from qlit.thesaurus import Thesaurus

if __name__ == '__main__':
    INDIR = '/Users/arildm/OneDrive-Shared/Olov Kriström - TTLs'
    # INDIR = 'ttls_test'

    # Prepare parsing.
    fns = [fn for fn in listdir(INDIR) if not fn.startswith('.')]
    print(f'Parsing {len(fns)} files...')
    thesaurus = Thesaurus()
    skipped = []

    # Parse input files.
    for fn in fns:
        # Skip non-RDF files.
        if fn.startswith('.'):
            continue

        try:
            # Why not thesaurus.parse(path)? Because then we cannot resolve parse errors by skipping the input file.
            # Graph.parse adds triples incrementally, so we'd get weird data. Better skip entire terms then, I think.
            term_graph = Graph().parse(join(INDIR, fn))
            thesaurus += term_graph
        except Exception as err:
            # Report error and skip this input file.
            print(f'{fn}: {type(err)} {err}')
            skipped.append(fn)

    # Done parsing.
    if skipped:
        print(f'WARNING: Skipped {len(skipped)} files')
    print(f'Parsed {len(fns) - len(skipped)} files')

    # TODO Complete relations

    # Write result.
    terms = thesaurus.refs()
    OUTFILE = 'qlit.ttl'
    print(f'Writing {len(terms)} terms...')
    thesaurus.serialize(OUTFILE)
    print(f'Wrote {OUTFILE}')

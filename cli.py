import argparse

from qlit.thesaurus import Thesaurus

# Commands:
# build: infiles *.ttl -> complete qlit.ttl
# - readfiles: path -> graph (warn and skip on validation fail)
# - complete: graph, options -> graph
# - writefile: graph, path -> O
# repl: qlit.ttl -> cli
# serve: qlit.ttl, config.ini/.env -> a running server

if __name__ == '__main__':
    argp = argparse.ArgumentParser(
        description='Tools for the QLIT thesaurus. Use `python -i cli.py` to interact.',)
    argp.add_argument('-i', default='qlit.ttl', help='Thesaurus RDF file')
    argp_sub = argp.add_subparsers(dest='command')

    args = argp.parse_args()

    if (args.i):
        th = Thesaurus().parse(args.i)

    # Experiments
    term = th.refs()[1]
    print(term)
    print('get_parents', th.get_parents(term).refs())
    print('get_children', th.get_children(term).refs())
    print('get_roots [:5]', th.get_roots().refs()[:5])

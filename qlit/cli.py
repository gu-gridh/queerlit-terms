import argparse

from rdflib import RDF, SKOS
from thesaurus import read_ttl, Term

if __name__ == '__main__':
    argp = argparse.ArgumentParser(
        description='Tools for the QLIT thesaurus.')
    argp.add_argument('--infile')
    # argp.add_argument('command')
    args = argp.parse_args()

    # Experiments
    graph = read_ttl(args.infile)
    terms = list(graph.subjects(RDF.type, SKOS.Concept))
    print(terms[1])
    term = Term(graph, 'https://queerlit.dh.gu.se/qlit/0.2/BDSMGemenskaper')
    print(term)

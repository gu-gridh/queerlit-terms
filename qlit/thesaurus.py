from typing import Iterator
from rdflib import RDF, SKOS, Graph, URIRef
from term import Term


def read_ttl(path: str) -> Graph:
    graph = Graph()
    graph.parse(path)
    return graph


def read_ttls(path: str) -> Graph:
    raise NotImplemented


def write_ttl(graph: Graph, path):
    raise NotImplemented


def complete_relations(graph: Graph) -> Graph:
    raise NotImplemented


def autocomplete(graph: Graph, q: str) -> Term:
    raise NotImplemented


def get_children(graph: Graph, term: Term) -> Iterator[Term]:
    term_ref = URIRef(term.uri)
    child_refs = graph.subjects(SKOS.broader, term_ref)
    for child_ref in child_refs:
        yield Term(graph, child_ref)


def get_parents(graph: Graph, term: Term) -> Iterator[Term]:
    term_ref = URIRef(term.uri)
    parent_refs = graph.objects(term_ref, SKOS.broader)
    for parent_ref in parent_refs:
        yield Term(graph, parent_ref)


def get_roots(graph: Graph) -> Iterator[Term]:
    term_refs = graph.subjects(RDF.type, SKOS.Concept)
    for term_ref in term_refs:
        if not next(graph.objects(term_ref, SKOS.broader), None):
            yield Term(graph, term_ref)

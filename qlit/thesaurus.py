from rdflib import Graph
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


def get_children(graph: Graph, term: Term) -> list[Term]:
    raise NotImplemented


def get_parents(graph: Graph, term: Term) -> list[Term]:
    raise NotImplemented


def get_roots(graph: Graph) -> list[Term]:
    return get_children(graph, None)

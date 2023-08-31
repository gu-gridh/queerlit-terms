from rdflib import Graph, DCTERMS, URIRef, Literal
from .qlit import qlit_validate_partial

def test_qlit_validate_partial():
    g = Graph()
    g.add((URIRef('example.com/foo/bar'), DCTERMS.identifier, Literal("bar"))) # Correct
    g.add((URIRef('example.com/foo/baz'), DCTERMS.identifier, Literal("qux"))) # Incorrect
    g.add((URIRef('example.com/foo/qux'), DCTERMS.identifier, Literal("baz"))) # Incorrect

    errors = list(qlit_validate_partial(g))
    assert len(errors) == 2
    assert errors[0] == 'Identifier "qux" != URI basename "baz"'
    assert errors[1] == 'Identifier "baz" != URI basename "qux"'
from rdflib import Graph, URIRef, Literal, RDF, SKOS
from .skos import skos_validate_partial, skos_validate_graph, skos_complete_graph
from .thesaurus import Thesaurus

def test_skos_validate_partial():
    g = Graph()
    g.add((URIRef("foo"), URIRef("label"), Literal("Foo"))) # Correct
    g.add((URIRef("foo"), URIRef("label:"), Literal("Foo"))) # Incorrect

    errors = list(skos_validate_partial(g))
    assert len(errors) == 1
    assert errors[0] == 'Predicate ends with colon: "label:"'

def test_skos_validate_graph():
    t = Thesaurus()
    t.add((URIRef("food"), RDF.type, SKOS.Concept))
    t.add((URIRef("fruit"), RDF.type, SKOS.Concept))
    t.add((URIRef("food"), SKOS.narrower, URIRef("fruit")))
    t.add((URIRef("food"), SKOS.narrower, URIRef("vegetable")))
    t.add((URIRef("fruit"), SKOS.broader, URIRef("plant")))
    t.add((URIRef("fruit"), SKOS.related, URIRef("vegetable")))
    t.add((URIRef("fruit"), SKOS.hasTopConcept, URIRef("food")))

    errors = list(skos_validate_graph(t))
    assert len(errors) == 4
    assert 'No such concept vegetable, core#narrower of food' in errors
    assert 'No such concept plant, core#broader of fruit' in errors
    assert 'No such concept vegetable, core#related of fruit' in errors
    assert 'Concept fruit must not have `hasTopConcept`' in errors

def test_skos_complete_graph():
    t = Thesaurus()
    food = URIRef("https://queerlit.dh.gu.se/qlit/v1/food")
    fruit = URIRef("https://queerlit.dh.gu.se/qlit/v1/fruit")
    vegetable = URIRef("https://queerlit.dh.gu.se/qlit/v1/vegetable")
    t.add((food, RDF.type, SKOS.Concept))
    t.add((fruit, RDF.type, SKOS.Concept))
    t.add((vegetable, RDF.type, SKOS.Concept))
    t.add((food, SKOS.narrower, fruit))
    t.add((vegetable, SKOS.broader, food))
    t.add((vegetable, SKOS.related, fruit))

    skos_complete_graph(t)
    assert (fruit, SKOS.inScheme, t.scheme) in t
    assert (fruit, SKOS.broader, food) in t
    assert (food, SKOS.narrower, vegetable) in t
    assert (fruit, SKOS.related, vegetable) in t
    assert (food, SKOS.topConceptOf, t.scheme) in t
    assert (fruit, SKOS.topConceptOf, t.scheme) not in t
    assert (t.scheme, SKOS.hasTopConcept, food) in t
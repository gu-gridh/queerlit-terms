from pytest import raises
from rdflib import URIRef, RDF, SKOS
from .thesaurus import Termset, Thesaurus, TermNotFoundError

def test_termset():
    t = Termset()
    t.add((URIRef("foo"), RDF.type, SKOS.Concept))
    t.add((URIRef("bar"), RDF.type, SKOS.Collection))
    t.add((URIRef("baz"), RDF.type, SKOS.ConceptScheme))

    refs = t.refs()
    assert len(refs) == 2
    assert URIRef("foo") in refs
    assert URIRef("bar") in refs

    concepts = t.concepts()
    assert len(concepts) == 1
    assert URIRef("foo") in concepts

    collections = t.collections()
    assert len(collections) == 1
    assert URIRef("bar") in collections

    assert t.assert_term_exists(URIRef("foo"))
    assert t.assert_term_exists(URIRef("bar"))
    with raises(TermNotFoundError):
        t.assert_term_exists(URIRef("baz"))

def create_thesaurus():
    t = Thesaurus()
    food = URIRef("https://queerlit.dh.gu.se/qlit/v1/food")
    fruit = URIRef("https://queerlit.dh.gu.se/qlit/v1/fruit")
    vegetable = URIRef("https://queerlit.dh.gu.se/qlit/v1/vegetable")
    vegetarian = URIRef("https://queerlit.dh.gu.se/qlit/v1/vegetarian")

    t.add((food, RDF.type, SKOS.Concept))
    t.add((fruit, RDF.type, SKOS.Concept))
    t.add((vegetable, RDF.type, SKOS.Concept))

    t.add((vegetarian, RDF.type, SKOS.Collection))
    t.add((vegetarian, SKOS.member, fruit))
    t.add((vegetarian, SKOS.member, vegetable))

    t.add((food, SKOS.narrower, fruit))
    t.add((vegetable, SKOS.broader, food))
    t.add((vegetable, SKOS.related, fruit))

    return (t, food, fruit, vegetable, vegetarian)

def test_thesaurus_terms_if():
    t, food, fruit, vegetable, vegetarian = create_thesaurus()
    termset = t.terms_if(lambda term: "f" in term)
    assert len(termset) == 3
    assert (food, RDF.type, SKOS.Concept) in termset
    assert (fruit, RDF.type, SKOS.Concept) in termset
    assert (food, SKOS.narrower, fruit) in termset

def test_thesaurus_get():
    t, food, fruit, vegetable, vegetarian = create_thesaurus()
    termset = t.get(food)
    assert len(termset) == 2
    assert (food, RDF.type, SKOS.Concept) in termset
    assert (food, SKOS.narrower, fruit) in termset

def test_thesaurus_get_collections():
    t, food, fruit, vegetable, vegetarian = create_thesaurus()
    termset = t.get_collections()
    assert len(termset) == 3
    assert (vegetarian, RDF.type, SKOS.Collection) in termset
    assert (vegetarian, SKOS.member, fruit) in termset
    assert (vegetarian, SKOS.member, vegetable) in termset

def test_thesaurus_get_roots():
    t, food, fruit, vegetable, vegetarian = create_thesaurus()
    termset = t.get_roots()
    assert len(termset) == 3
    assert (food, RDF.type, SKOS.Concept) in termset
    assert (fruit, RDF.type, SKOS.Concept) in termset
    assert (food, SKOS.narrower, fruit) in termset

def test_thesaurus_get_narrower():
    t, food, fruit, vegetable, vegetarian = create_thesaurus()
    termset = t.get_narrower(food)
    assert len(termset) == 1
    assert (fruit, RDF.type, SKOS.Concept) in termset
    assert len(t.get_narrower(fruit)) == 0
    with raises(TermNotFoundError):
        t.get_narrower(URIRef("banana"))

def test_thesaurus_get_broader():
    t, food, fruit, vegetable, vegetarian = create_thesaurus()
    termset = t.get_broader(vegetable)
    assert len(termset) == 2
    assert (food, RDF.type, SKOS.Concept) in termset
    assert (food, SKOS.narrower, fruit) in termset
    assert len(t.get_broader(food)) == 0
    with raises(TermNotFoundError):
        t.get_broader(URIRef("banana"))

def test_thesaurus_get_related():
    t, food, fruit, vegetable, vegetarian = create_thesaurus()
    termset = t.get_related(vegetable)
    assert len(termset) == 1
    assert (fruit, RDF.type, SKOS.Concept) in termset
    assert len(t.get_related(food)) == 0
    with raises(TermNotFoundError):
        t.get_related(URIRef("banana"))

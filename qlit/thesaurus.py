from rdflib import RDF, SKOS, Graph, Literal, URIRef

BASE = 'https://queerlit.dh.gu.se/qlit/v1/'


class Termset(Graph):
    """All the triples for a selected subset of the terms."""

    def refs(self) -> list[URIRef]:
        """The URIRefs of the included terms."""
        return [s for (s, p, o) in self if p == RDF.type and o in (SKOS.Concept, SKOS.Collection)]

    def concepts(self) -> list[URIRef]:
        """The URIRefs of the included terms."""
        return list(self.subjects(RDF.type, SKOS.Concept))

    def collections(self) -> list[URIRef]:
        """The URIRefs of the included collections."""
        return list(self.subjects(RDF.type, SKOS.Collection))

    def assert_term_exists(self, ref):
        if not ref in self.refs():
            raise TermNotFoundError(ref)
        return True

class Thesaurus(Termset):
    """An RDF graph indended to contain a full thesaurus."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base = BASE
        self.scheme = URIRef(self.base.rstrip('/'))
        self.add((self.scheme, RDF.type, SKOS.ConceptScheme))
        self.add((self.scheme, SKOS.prefLabel, Literal("Queerlit")))
        self.add((self.scheme, SKOS.notation, Literal("qlit")))

    def terms_if(self, f) -> Termset:
        """Creates a subset with terms matching some condition."""
        g = Termset(base=self.base)
        for term in self.refs():
            if f(term):
                g += self.triples((term, None, None))
        return g

    def get(self, ref: URIRef) -> Termset:
        """Get the triples of a single term."""
        self.assert_term_exists(ref)
        return self.terms_if(lambda term: term == ref)

    def get_collections(self) -> Termset:
        """Find all collections."""
        g = Termset(base=self.base)
        for ref in self.collections():
            g += self.triples((ref, None, None))
        return g

    def get_roots(self) -> Termset:
        """Find all terms without parents."""
        return self.terms_if(lambda term: self[term:RDF.type:SKOS.Concept] and not self.value(term, SKOS.broader))

    def get_narrower(self, broader: URIRef) -> Termset:
        """Find terms that are directly narrower than a given term."""
        self.assert_term_exists(broader)
        return self.terms_if(lambda term: self[broader:SKOS.narrower:term])

    def get_broader(self, narrower: URIRef) -> Termset:
        """Find terms that are directly broader than a given term."""
        self.assert_term_exists(narrower)
        return self.terms_if(lambda term: self[narrower:SKOS.broader:term])

    def get_related(self, other: URIRef) -> Termset:
        """Find terms that are related to a given term."""
        self.assert_term_exists(other)
        return self.terms_if(lambda term: self[other:SKOS.related:term])


class TermNotFoundError(KeyError):
    def __init__(self, term_uri, *args):
        self.term_uri = term_uri

    def __str__(self):
        return f'Term not found: {self.term_uri}'
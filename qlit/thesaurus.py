from rdflib import DCTERMS, RDF, SKOS, Graph, URIRef

BASE = 'https://queerlit.dh.gu.se/qlit/0.2/'


class Termset(Graph):
    """All the triples for a selected subset of the terms."""

    def refs(self) -> list[URIRef]:
        """The URIRefs of the included terms."""
        return list(self.subjects(RDF.type, SKOS.Concept))


class Thesaurus(Termset):
    """An RDF graph indended to contain a full thesaurus."""
    # TODO Source files use "dc" for "dcterms", resulting in a conflict which results in "dc1" in the output. Is that ok?

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base = BASE

    def complete_relations() -> "Thesaurus":
        """Add triples to ensure that all term-term relations are two-way."""
        # broader <-> narrower
        # set inScheme
        # ajust topConceptOf
        # topConceptOf <-> hasTopConcept
        # related <-> related (or not?)
        raise NotImplemented

    def terms_if(self, f) -> Termset:
        """Creates a subset with terms matching some condition."""
        g = Termset(base=self.base)
        for term in self.refs():
            if f(term):
                g += self.triples((term, None, None))
        return g

    def get(self, ref: URIRef) -> Termset:
        """Get the triples of a single term."""
        return self.terms_if(lambda term: term == ref)

    def get_roots(self) -> Termset:
        """Find all terms without parents."""
        return self.terms_if(lambda term: (term, SKOS.broader, None) not in self)

    def get_parents(self, child: URIRef) -> Termset:
        """Find terms that are directly broader than a given term."""
        return self.terms_if(lambda term: (child, SKOS.broader, term) in self)

    def get_children(self, parent: URIRef) -> Termset:
        """Find terms that are directly narrower than a given term."""
        return self.terms_if(lambda term: (term, SKOS.broader, parent) in self)

    def autocomplete(q: str) -> Termset:
        """Find terms matching a user-given incremental (startswith) search string."""
        raise NotImplemented

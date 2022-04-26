from rdflib import RDF, SKOS, Graph, URIRef


class Termset(Graph):
    """All the triples for a selected subset of the terms."""

    def refs(self) -> list[URIRef]:
        """The URIRefs of the included terms."""
        return list(self.subjects(RDF.type, SKOS.Concept))


class Thesaurus(Termset):
    """An RDF graph indended to contain a full thesaurus."""

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
        g = Termset()
        for term in self.refs():
            if f(term):
                g += self.triples((term, None, None))
        return g

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

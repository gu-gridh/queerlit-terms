from rdflib import RDF, SKOS, Graph, URIRef


class Termset(Graph):
    def refs(self) -> list[URIRef]:
        return list(self.subjects(RDF.type, SKOS.Concept))


class Thesaurus(Termset):
    def complete_relations(graph: Graph) -> Graph:
        raise NotImplemented

    def terms_if(self, f) -> Termset:
        g = Termset()
        for term in self.refs():
            if f(term):
                g += self.triples((term, None, None))
        return g

    def get_roots(self) -> Termset:
        return self.terms_if(lambda term: (term, SKOS.broader, None) not in self)

    def get_parents(self, child: URIRef) -> Termset:
        return self.terms_if(lambda term: (child, SKOS.broader, term) in self)

    def get_children(self, parent: URIRef) -> Termset:
        return self.terms_if(lambda term: (term, SKOS.broader, parent) in self)

    def autocomplete(q: str) -> Termset:
        raise NotImplemented

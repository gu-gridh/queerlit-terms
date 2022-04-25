from rdflib import SKOS, Graph, URIRef


class Term:
    def __init__(self, graph: Graph, uri: str):
        ref = URIRef(uri)
        self.uri = uri
        self.prefLabel = graph.value(ref, SKOS.prefLabel)
        self.altLabels = graph.objects(ref, SKOS.altLabel)
        self.scopeNote = graph.value(ref, SKOS.scopeNote)

    def __str__(self):
        return self.prefLabel

    def __repr__(self):
        return f'<Term {self.prefLabel}>'

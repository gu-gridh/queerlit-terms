from rdflib import SKOS, Graph, URIRef


class Term:
    def __init__(self, graph: Graph, uri: str):
        ref = URIRef(uri)
        self.uri = uri
        self.prefLabel = next(graph.objects(ref, SKOS.prefLabel))
        self.altLabels = list(graph.objects(ref, SKOS.altLabel))
        self.scopeNote = next(graph.objects(ref, SKOS.scopeNote))

    def __str__(self):
        return f'<{self.prefLabel}>'

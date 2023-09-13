from os.path import basename
from rdflib import Graph, SKOS, RDF, DCTERMS
from qlit.thesaurus import Thesaurus
from collections.abc import Generator

# There's of course more constraints in the SKOS definition than this.

def skos_validate_partial(g: Graph) -> Generator[str]:
  # Catch common syntax mistake
  for s, p, o in g:
    if p.endswith(':'):
      yield f'Predicate ends with colon: "{p}"'


def skos_validate_graph(g: Thesaurus) -> Generator[str]:
  for term in g.refs():
    for rel in [SKOS.broader, SKOS.narrower, SKOS.related]:
      for other in g.objects(term, rel):
        if not g[other:RDF.type:SKOS.Concept]:
          yield f'No such concept {basename(other)}, {basename(rel)} of {basename(term)}'
    if g.value(term, SKOS.hasTopConcept):
      yield f'Concept {basename(term)} must not have `hasTopConcept`'


def skos_complete_graph(g: Thesaurus) -> None:
  for term in g.refs():
    # set inScheme
    g.set((term, SKOS.inScheme, g.scheme))

  for term in g.concepts():
    # broader <-> narrower
    for broader in g[term:SKOS.broader]:
      g.add((broader, SKOS.narrower, term))
    for narrower in g[term:SKOS.narrower]:
      g.add((narrower, SKOS.broader, term))

    # related <-> related
    for relatee in g[term:SKOS.related]:
      g.add((relatee, SKOS.related, term))

    # topConceptOf <-> hasTopConcept
    g.remove((term, SKOS.topConceptOf, None))
    if not g.value(term, SKOS.broader):
      g.set((term, SKOS.topConceptOf, g.scheme))
      g.add((g.scheme, SKOS.hasTopConcept, term))

    # replaces <-> isReplacedBy
    for replaced in g[term:DCTERMS.replaces]:
      g.add((replaced, DCTERMS.isReplacedBy, term))
    for replacer in g[term:DCTERMS.isReplacedBy]:
      g.add((replacer, DCTERMS.replaces, term))
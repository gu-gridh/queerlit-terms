from os.path import basename
from rdflib import Graph, DCTERMS
from collections.abc import Generator

def qlit_validate_partial(g: Graph) -> Generator[str]:
  # validate identifiers
  for term, identifier in g[:DCTERMS.identifier:]:
    name = basename(term)
    if name != str(identifier):
      yield f'Identifier "{identifier}" != URI basename "{name}"'

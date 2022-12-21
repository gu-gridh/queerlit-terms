"""
Non-RDF interfaces to the thesaurus.
"""

from os.path import basename
import re
from rdflib import SKOS, URIRef
from qlit.thesaurus import BASE, Termset, Thesaurus


HOMOSAURUS = Thesaurus().parse('homosaurus.ttl')


def name_to_ref(name: str) -> URIRef:
    return URIRef(BASE + name)


def ref_to_name(ref: URIRef) -> str:
    return basename(ref)


def resolve_external_term(ref):
    if ref.startswith('https://homosaurus.org/v3/'):
        return resolve_homosaurus_term(ref)
    return {
        'uri': str(ref),
    }


def resolve_homosaurus_term(ref):
    prefLabel = HOMOSAURUS.value(ref, SKOS.prefLabel)
    altLabels = list(HOMOSAURUS.objects(ref, SKOS.altLabel))
    return {
        'uri': str(ref),
        'prefLabel': prefLabel,
        'altLabels': altLabels,
    }


class SimpleTerm(dict):

    @staticmethod
    def from_subject(termset: Termset, subject: URIRef) -> "SimpleTerm":
        """Make a simple dict with the predicate-objects of a term in the thesaurus."""
        termset.assert_term_exists(subject)
        return SimpleTerm(
            name=ref_to_name(subject),
            uri=str(subject),
            prefLabel=termset.value(subject, SKOS.prefLabel),
            altLabels=list(termset.objects(subject, SKOS.altLabel)),
            scopeNote=termset.value(subject, SKOS.scopeNote),
            # Relations to QLIT terms
            broader=[ref_to_name(ref)
                     for ref in termset.objects(subject, SKOS.broader)],
            narrower=[ref_to_name(ref)
                      for ref in termset.objects(subject, SKOS.narrower)],
            related=[ref_to_name(ref)
                     for ref in termset.objects(subject, SKOS.related)],
            # Relations to external terms
            exactMatch=[resolve_external_term(ref) for ref in termset.objects(subject, SKOS.exactMatch)],
            closeMatch=[resolve_external_term(ref) for ref in termset.objects(subject, SKOS.closeMatch)],
        )

    @staticmethod
    def from_termset(termset: Termset) -> list["SimpleTerm"]:
        """Make simple dicts for the given set of terms."""
        return [
            SimpleTerm.from_subject(termset, ref)
            for ref in termset.refs()
        ]


class SimpleThesaurus(Thesaurus):
    """Like Thesaurus but with unqualified names as inputs and dicts as output."""

    def get_simple_terms(self):
        self.simple_terms = SimpleTerm.from_termset(self)
        return self.simple_terms

    def terms_if(self, f) -> list[SimpleTerm]:
        return SimpleTerm.from_termset(super().terms_if(f))

    def get(self, name: str) -> SimpleTerm:
        return SimpleTerm.from_subject(self, name_to_ref(name))

    def get_children(self, parent: str) -> list[SimpleTerm]:
        return super().get_children(name_to_ref(parent))

    def get_parents(self, child: str) -> list[SimpleTerm]:
        return super().get_parents(name_to_ref(child))

    def get_related(self, other: str) -> list[SimpleTerm]:
        return super().get_related(name_to_ref(other))

    def get_all(self) -> list[SimpleTerm]:
        """All terms as dicts."""
        return SimpleTerm.from_termset(self)

    def autocomplete(self, s: str) -> Termset:
        """Find terms matching a user-given incremental (startswith) search string."""
        ignore_re = re.compile(r'[ -/()]')
        def split_label(string):
            return list(filter(bool, ignore_re.split(string)))

        search_words = split_label(s)

        def term_labels(term):
            if term.get('prefLabel'):
                yield term['prefLabel']
            if term.get('altLabels'):
                yield from term['altLabels']
            if 'exactMatch' in term:
                for match in term['exactMatch']:
                    yield from term_labels(match)

        def is_match(term):
            # Match with all words in the query
            return all(
                # Match against any word in the term
                any(
                    term_word.lower().startswith(search_word.lower())
                    for label in term_labels(term)
                    for term_word in split_label(label))
                for search_word in search_words)

        return [term for term in self.get_simple_terms() if is_match(term)]

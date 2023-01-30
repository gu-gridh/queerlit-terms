"""
Non-RDF interfaces to the thesaurus.
"""

from os.path import basename
import re
from rdflib import SKOS, URIRef
from qlit.thesaurus import BASE, Termset, Thesaurus


HOMOSAURUS = Thesaurus().parse('homosaurus.ttl')


class Tokenizer:
    DELIMITER = re.compile(r'[ -/()]')

    @classmethod
    def split(cls, phrase):
        return filter(None, cls.DELIMITER.split(phrase))


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
            hiddenLabels=list(termset.objects(subject, SKOS.hiddenLabel)),
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rebuild()

    def rebuild(self):
        self.build_simple_terms()
        self.build_search_index()

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
        search_words = list(Tokenizer.split(s))

        def is_match(term_words):
            # Match with all words in the query
            return all(
                # Match against any word in the term
                any(term_word.startswith(search_word)
                    for term_word in term_words)
                for search_word in search_words)

        return [self.simple_terms[name] for name in self.index if is_match(self.index[name])]

    def build_simple_terms(self):
        self.simple_terms = dict()
        for simple_term in SimpleTerm.from_termset(self):
            self.simple_terms[simple_term['name']] = simple_term

    def build_search_index(self):
        self.index = dict()

        def term_labels(term):
            if term.get('prefLabel'):
                yield term['prefLabel']
            if term.get('altLabels'):
                yield from term['altLabels']
            if term.get('hiddenLabels'):
                yield from term['hiddenLabels']
            if 'exactMatch' in term:
                for match in term['exactMatch']:
                    yield from term_labels(match)

        for name, term in self.simple_terms.items():
            self.index[name] = []
            for label in term_labels(term):
                for term_word in Tokenizer.split(label):
                    self.index[name].append(term_word.lower())

        return self.index
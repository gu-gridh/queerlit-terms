"""
Non-RDF interfaces to the thesaurus.
"""

from os.path import basename
from os import environ
import time
import re
from dotenv import load_dotenv
from rdflib import SKOS, URIRef, Literal
from qlit.thesaurus import BASE, Termset, Thesaurus
from collections.abc import Generator


load_dotenv()


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
    return SimpleTerm(uri=str(ref))


def resolve_homosaurus_term(ref):
    prefLabel = HOMOSAURUS.value(ref, SKOS.prefLabel)
    altLabels = list(HOMOSAURUS.objects(ref, SKOS.altLabel))
    return SimpleTerm(
        uri=str(ref),
        prefLabel=prefLabel,
        altLabels=altLabels
    )


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
        terms = [SimpleTerm.from_subject(termset, ref) for ref in termset.refs()]
        terms.sort(key=lambda term: term['prefLabel'].lower())
        return terms

    def get_labels(self) -> Generator[Literal]:
        """Labels for the term (or for closely related concepts), in relevance order."""
        match: SimpleTerm
        if self.get('prefLabel'):
            yield self['prefLabel']
        if 'exactMatch' in self:
            for match in self['exactMatch']:
                yield from match.get_labels()
        if self.get('altLabels'):
            yield from self['altLabels']
        if self.get('hiddenLabels'):
            yield from self['hiddenLabels']
        if 'closeMatch' in self:
            for match in self['closeMatch']:
                yield from match.get_labels()

    def get_words(self) -> Generator[str]:
        """All the labels for this term, tokenized into words and lowercased."""
        for label in self.get_labels():
            for word in Tokenizer.split(label):
                yield word.lower()


class SimpleThesaurus(Thesaurus):
    """Like Thesaurus but with unqualified names as inputs and dicts as output."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.simple_terms = None
        self.index = None

    def rebuild(self):
        if environ.get("FLASK_DEBUG"):
            print('Building simple terms... ', end="", flush=True)
        tic = time.time()
        self.build_simple_terms()
        if environ.get("FLASK_DEBUG"):
            print("%.2fs" % (time.time() - tic,))

        if environ.get("FLASK_DEBUG"):
            print('Building search index... ', end="", flush=True)
        tic = time.time()
        self.build_search_index()
        if environ.get("FLASK_DEBUG"):
            print("%.2fs" % (time.time() - tic,))

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
        if not self.simple_terms:
            self.rebuild()

        search_words = [word.lower() for word in Tokenizer.split(s)]

        def is_match(term_words):
            # Match with all words in the query
            return all(
                # Match against any word in the term
                any(term_word.startswith(search_word)
                    for term_word in term_words)
                for search_word in search_words)

        # Get subset of terms that matches the query.
        terms = [self.simple_terms[name] for name in self.index if is_match(self.index[name])]

        def score(term : SimpleTerm) -> float:
            """Calculate match score."""
            # Map each word in the term to whether it contributes to the match.
            term_word_hits = [any(t.startswith(s) for s in search_words) for t in term.get_words()]
            # Score early matching words more than late ones.
            score = sum(int(hit) / i for i, hit in enumerate(term_word_hits, start=1))
            # Add a small bonus for root terms. Not sure if this is motivated.
            score += 0.1 if len(term['broader']) == 0 else 0
            return score

        # Clone terms so that changes do not affect the originals.
        terms = [SimpleTerm(**term) for term in terms]

        # Calculate match score and add it to the term dict.
        for term in terms:
            term['score'] = score(term)

        # Sort alphabetically first.
        terms.sort(key=lambda term: term['prefLabel'].lower())
        # More significantly, sort descending by match score.
        terms.sort(key=lambda term: term['score'], reverse=True)
        return terms

    def get_collections(self):
        g = super().get_collections()
        dicts = [dict(
            name=ref_to_name(ref),
            uri=str(ref),
            prefLabel=g.value(ref, SKOS.prefLabel),
        ) for ref in g.collections()]
        dicts.sort(key=lambda term: term['prefLabel'].lower())
        return dicts

    def get_collection(self, name, tree=False):
        ref = name_to_ref(name)
        terms = self.terms_if(lambda term: self[ref:SKOS.member:term])
        if tree:
            self.expand_narrower(terms)
        return terms

    def get_labels(self):
        """All term labels, keyed by corresponding term identifiers."""
        if not self.simple_terms:
            self.rebuild()
        return dict((name, term['prefLabel']) for (name, term) in self.simple_terms.items())

    def build_simple_terms(self):
        self.simple_terms : dict[str, SimpleTerm] = dict()
        for simple_term in SimpleTerm.from_termset(self):
            self.simple_terms[simple_term['name']] = simple_term

    def build_search_index(self):
        self.index : dict[str, list[str]] = dict()

        for name, term in self.simple_terms.items():
            self.index[name] = []
            for word in term.get_words():
                self.index[name].append(word)

        return self.index

    def expand_narrower(self, terms: list[SimpleTerm]):
        """Instead of string names, look up and inflate narrower terms recursively."""
        for term in terms:
            expanded = []
            for name in term["narrower"]:
                expanded.append(self.get(name))
            self.expand_narrower(expanded)
            term["narrower"] = expanded

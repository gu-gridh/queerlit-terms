"""
Non-RDF interfaces to the thesaurus.
"""

from os.path import basename
from os import environ
import time
import re
from dotenv import load_dotenv
from rdflib import SKOS, URIRef, Literal
from .thesaurus import BASE, Termset, Thesaurus
from .search import Searcher
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


class SimpleThesaurus():
    """Like Thesaurus but with unqualified names as inputs and dicts as output."""

    def __init__(self, thesaurus: Thesaurus):
        self.t = thesaurus
        self.simple_terms = None
        self.searcher = None
        self.rebuild()

    def rebuild(self):
        if environ.get("FLASK_DEBUG"):
            print('Building simple terms... ', end="", flush=True)
        tic = time.time()
        self.build_simple_terms()
        if environ.get("FLASK_DEBUG"):
            print("%.2fs" % (time.time() - tic,))

        self.searcher = Searcher(self.simple_terms.values(), lambda term: term.get_words())

    def get(self, name: str) -> SimpleTerm:
        return SimpleTerm.from_subject(self.t, name_to_ref(name))

    def get_roots(self) -> Termset:
        """Find all terms without parents."""
        termset = self.t.get_roots()
        return SimpleTerm.from_termset(termset)

    def get_narrower(self, broader: str) -> list[SimpleTerm]:
        ref = name_to_ref(broader)
        termset = self.t.get_narrower(ref)
        return SimpleTerm.from_termset(termset)

    def get_broader(self, narrower: str) -> list[SimpleTerm]:
        ref = name_to_ref(narrower)
        termset = self.t.get_broader(ref)
        return SimpleTerm.from_termset(termset)

    def get_related(self, other: str) -> list[SimpleTerm]:
        ref = name_to_ref(other)
        termset = self.t.get_related(ref)
        return SimpleTerm.from_termset(termset)

    def search(self, s: str) -> Termset:
        """Find terms matching a user-given incremental (startswith) search string."""
        scored_hits = self.searcher.search(s)
        hits = []
        for (score, hit) in scored_hits:
            hit["score"] = score
            hits.append(hit)
        return hits

    def get_collections(self):
        g = self.t.get_collections()
        dicts = [dict(
            name=ref_to_name(ref),
            uri=str(ref),
            prefLabel=g.value(ref, SKOS.prefLabel),
        ) for ref in g.collections()]
        dicts.sort(key=lambda term: term['prefLabel'].lower())
        return dicts

    def get_collection(self, name, tree=False):
        ref = name_to_ref(name)
        termset = self.t.terms_if(lambda term: self.t[ref:SKOS.member:term])
        terms = SimpleTerm.from_termset(termset)
        if tree:
            self.expand_narrower(terms)
        return terms

    def get_labels(self):
        """All term labels, keyed by corresponding term identifiers."""
        return dict((ref_to_name(name), label) for (name, label) in self.t.subject_objects(SKOS.prefLabel))

    def build_simple_terms(self):
        self.simple_terms : dict[str, SimpleTerm] = dict()
        for simple_term in SimpleTerm.from_termset(self.t):
            self.simple_terms[simple_term['name']] = simple_term

    def expand_narrower(self, terms: list[SimpleTerm]):
        """Instead of string names, look up and inflate narrower terms recursively."""
        for term in terms:
            expanded = []
            for name in term["narrower"]:
                expanded.append(self.get(name))
            self.expand_narrower(expanded)
            term["narrower"] = expanded

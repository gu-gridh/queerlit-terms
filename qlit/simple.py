"""
Non-RDF interfaces to the thesaurus.
"""

from os.path import basename
import re
from dotenv import load_dotenv
from rdflib import SKOS, URIRef, Literal
from .thesaurus import BASE, Termset, Thesaurus
from math import log
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
        self.th = Thesaurus()
        self.th += self.t + HOMOSAURUS

    def get(self, name: str) -> SimpleTerm:
        ref = name_to_ref(name)
        self.t.assert_term_exists(ref)
        return SimpleTerm.from_subject(self.t, name_to_ref(name))

    def get_roots(self) -> Termset:
        """Find all terms without parents."""
        termset = self.t.get_roots()
        return SimpleTerm.from_termset(termset)

    def get_narrower(self, broader: str) -> list[SimpleTerm]:
        ref = name_to_ref(broader)
        self.t.assert_term_exists(ref)
        termset = self.t.get_narrower(ref)
        return SimpleTerm.from_termset(termset)

    def get_broader(self, narrower: str) -> list[SimpleTerm]:
        ref = name_to_ref(narrower)
        self.t.assert_term_exists(ref)
        termset = self.t.get_broader(ref)
        return SimpleTerm.from_termset(termset)

    def get_related(self, other: str) -> list[SimpleTerm]:
        ref = name_to_ref(other)
        self.t.assert_term_exists(ref)
        termset = self.t.get_related(ref)
        return SimpleTerm.from_termset(termset)

    def search(self, s: str) -> Termset:
        """Find terms matching a user-given incremental (startswith) search string."""
        qws = list(Tokenizer.split(s.lower()))

        def match(label: str) -> float:
            lws = Tokenizer.split(label.lower())
            for i, lw in enumerate(lws):
                if any(lw.startswith(qw) for qw in qws):
                    # Score more if match appears early in label
                    return 10 - min(i, 5)
            return 0


        hits = dict()
        def add_hit(ref, score):
            if not ref in hits:
                hits[ref] = 0
            hits[ref] = max(hits[ref], score)

        fields = {
            SKOS.prefLabel: 1,
            SKOS.altLabel: .8,
            SKOS.hiddenLabel: .6,
        }
        for ref, p, label in self.th:
            if p not in fields.keys(): continue

            score = match(label) * fields[p]
            if not score: continue

            if (ref.startswith("https://queerlit")):
                add_hit(ref, score)
            for sref in self.th.subjects(SKOS.exactMatch, ref):
                add_hit(sref, score * .8)
            for sref in self.th.subjects(SKOS.closeMatch, ref):
                add_hit(sref, score * .5)

        scored_hits = []
        for ref, score in hits.items():
            term = SimpleTerm.from_subject(self.t, ref)
            term['score'] = score
            scored_hits.append(term)
        return sorted(scored_hits, key=lambda term: term['score'], reverse=True)

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
        self.t.assert_term_exists(ref)
        termset = self.t.terms_if(lambda term: self.t[ref:SKOS.member:term])
        terms = SimpleTerm.from_termset(termset)
        if tree:
            self.expand_narrower(terms)
        return terms

    def get_labels(self):
        """All term labels, keyed by corresponding term identifiers."""
        return dict((ref_to_name(name), label) for (name, label) in self.t.subject_objects(SKOS.prefLabel))

    def expand_narrower(self, terms: list[SimpleTerm]):
        """Instead of string names, look up and inflate narrower terms recursively."""
        for term in terms:
            expanded = []
            for name in term["narrower"]:
                expanded.append(self.get(name))
            self.expand_narrower(expanded)
            term["narrower"] = expanded

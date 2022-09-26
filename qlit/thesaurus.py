from itertools import chain
from os.path import basename
import re
from rdflib import DCTERMS, RDF, SKOS, Graph, Literal, URIRef

BASE = 'https://queerlit.dh.gu.se/qlit/v1/'


class Termset(Graph):
    """All the triples for a selected subset of the terms."""

    def refs(self) -> list[URIRef]:
        """The URIRefs of the included terms."""
        return list(self.subjects(RDF.type, SKOS.Concept))

    def assert_term_exists(self, ref):
        if not ref in self.refs():
            raise TermNotFoundError(ref)
        return True

class Thesaurus(Termset):
    """An RDF graph indended to contain a full thesaurus."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base = BASE
        self.scheme = URIRef(self.base.rstrip('/'))
        self.add((self.scheme, RDF.type, SKOS.ConceptScheme))
        self.add((self.scheme, SKOS.prefLabel, Literal("Queerlit")))
        self.add((self.scheme, SKOS.notation, Literal("qlit")))

    def complete_relations(self) -> "Thesaurus":
        """Add triples to ensure that all term-term relations are two-way."""

        def exists_or_warn(s_term, p_label, o_term):
            s = s_term.split('/')[-1]
            o = o_term.split('/')[-1]
            if o_term not in self.refs():
                print(f'WARNING: Missing {o} ({p_label} in {s})')
                return False
            return True

        for term in self.refs():
            # broader <-> narrower
            for parent in self.objects(term, SKOS.broader):
                if exists_or_warn(term, 'broader', parent):
                    self.add((parent, SKOS.narrower, term))

            for child in self.objects(term, SKOS.narrower):
                if exists_or_warn(term, 'narrower', child):
                    self.add((child, SKOS.broader, term))

            # related <-> related
            for relatee in self.objects(term, SKOS.related):
                if exists_or_warn(term, 'related', relatee):
                    self.add((relatee, SKOS.related, term))

            # set inScheme
            self.set((term, SKOS.inScheme, self.scheme))

            # adjust topConceptOf
            # topConceptOf <-> hasTopConcept
            self.remove((term, SKOS.topConceptOf, None))
            if list(self.objects(term, SKOS.hasTopConcept)):
                print(f'WARNING: Term {term} must not use hasTopConcept')
                self.remove((term, SKOS.hasTopConcept, None))
            if not list(self.objects(term, SKOS.broader)):
                self.set((term, SKOS.topConceptOf, self.scheme))
                self.add((self.scheme, SKOS.hasTopConcept, term))

            # validate identifiers
            name = basename(term)
            identifier = str(self.value(term, DCTERMS.identifier))
            if name != identifier:
                print(f'Identifier "{identifier}" != URI basename "{name}"')

    def terms_if(self, f) -> Termset:
        """Creates a subset with terms matching some condition."""
        g = Termset(base=self.base)
        for term in self.refs():
            if f(term):
                g += self.triples((term, None, None))
        return g

    def get(self, ref: URIRef) -> Termset:
        """Get the triples of a single term."""
        self.assert_term_exists(ref)
        return self.terms_if(lambda term: term == ref)

    def get_roots(self) -> Termset:
        """Find all terms without parents."""
        return self.terms_if(lambda term: (term, SKOS.broader, None) not in self)

    def get_children(self, parent: URIRef) -> Termset:
        """Find terms that are directly narrower than a given term."""
        self.assert_term_exists(parent)
        return self.terms_if(lambda term: (term, SKOS.broader, parent) in self)

    def get_parents(self, child: URIRef) -> Termset:
        """Find terms that are directly broader than a given term."""
        self.assert_term_exists(child)
        return self.terms_if(lambda term: (child, SKOS.broader, term) in self)

    def get_related(self, other: URIRef) -> Termset:
        """Find terms that are related to a given term."""
        self.assert_term_exists(other)
        return self.terms_if(lambda term: (term, SKOS.related, other) in self)

    def autocomplete(self, s: str) -> Termset:
        """Find terms matching a user-given incremental (startswith) search string."""
        ignore_re = re.compile(r'[ -/()]')
        def split_label(string):
            return list(filter(bool, ignore_re.split(string)))

        search_words = split_label(s)

        def term_labels(term):
            label = self.value(term, SKOS.prefLabel)
            altLabels = self.objects(term, SKOS.altLabel)
            return [label] + list(altLabels)

        def is_match(term):
            # Match with all words in the query
            return all(
                # Match against any word in the term
                any(
                    term_word.lower().startswith(search_word.lower())
                    for label in term_labels(term)
                    for term_word in split_label(label))
                for search_word in search_words)

        return self.terms_if(is_match)

class TermNotFoundError(KeyError):
    def __init__(self, term_uri, *args):
        self.term_uri = term_uri

    def __str__(self):
        return f'Term not found: {self.term_uri}'
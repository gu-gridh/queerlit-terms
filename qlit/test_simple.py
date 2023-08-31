from rdflib import URIRef
from .thesaurus import Thesaurus
from .simple import SimpleThesaurus, SimpleTerm, ref_to_name, name_to_ref, Tokenizer

def test_tokenizer():
    assert list(Tokenizer.split("foo bar")) == ["foo", "bar"]
    assert list(Tokenizer.split("foo-bar/baz")) == ["foo", "bar", "baz"]
    assert list(Tokenizer.split("MC-klubbar (HBTQI)")) == ["MC", "klubbar", "HBTQI"]

def test_ref_to_name():
    name = "foobar"
    ref = URIRef("https://queerlit.dh.gu.se/qlit/v1/" + name)
    assert name_to_ref(name) == ref
    assert ref_to_name(ref) == name

T = Thesaurus().parse('qlit.nt')
TS = SimpleThesaurus(T)

def test_simple_term_from_subject():
  uri = "https://queerlit.dh.gu.se/qlit/v1/ez04as46"
  term = SimpleTerm.from_subject(T, URIRef(uri))
  assert term["name"] == "ez04as46"
  assert term["uri"] == uri
  assert term["prefLabel"] == "Syskon"
  assert term["altLabels"] == []
  assert term["hiddenLabels"] == []
  assert term["scopeNote"] == "Används för skildringar av relationer mellan och till syskon."
  assert term["broader"] == ["um90bw50"]
  assert term["narrower"] == ["ow08sf46"]
  assert term["related"] == ["sr56ul39"]
  assert term["exactMatch"] == [{
      "altLabels": [],
      "prefLabel": "Siblings",
      "uri": "https://homosaurus.org/v3/homoit0001310"
  }]
  assert { "uri": "http://id.loc.gov/authorities/subjects/sh85017225" } in term["closeMatch"]
  assert { "uri": "https://id.kb.se/term/barn/Syskon" } in term["closeMatch"]
  assert { "uri": "https://id.kb.se/term/sao/Syskon" } in term["closeMatch"]
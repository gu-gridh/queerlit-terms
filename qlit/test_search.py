from .search import Searcher

def test_searcher():
    items = [
        { "title": "Silence of the Lambs", "actors": ["Jodie Foster", "Anthony Hopkins", "Lawrence A. Bonney"] },
        { "title": "Barbie", "actors": ["Margot Robbie", "Ryan Gosling"] },
        { "title": "Fargo", "actors": ["William H. Macy", "Frances McDormand", "Steve Buscemi"] },
    ]
    def get_strings(film):
        return [film["title"]] + film["actors"]

    s = Searcher(items, get_strings)
    assert len(s._items) == 3
    assert s._items == items

    assert list(s.tokenize("foo bar-baz")) == ['foo', 'bar', 'baz']

    assert s.match(["foo", "bar"], "food")
    assert not s.match(["foo", "bar"], "ba")

    hits = list(s.search('f'))
    assert len(hits) == 2
    assert hits[0][0] > hits[1][0]
    assert hits[0][1] == items[2]
    assert hits[1][1] == items[0]

    assert len(s._items) == 3
    assert s._items == items

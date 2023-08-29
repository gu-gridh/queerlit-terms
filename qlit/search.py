import re
from typing import TypeVar
from collections.abc import Callable

Item = TypeVar('Item')

class Searcher:
    DELIMITER = re.compile(r'[ -/()]')

    def __init__(self, items: list[Item], get_strings: Callable[[Item], list[str]]):
        self._items = items
        self._get_strings = get_strings

    @classmethod
    def tokenize(cls, phrase: str) -> list[str]:
        return filter(None, cls.DELIMITER.split(phrase))

    def search(self, q: str) -> list[tuple[int, Item]]:
        qws = list(self.tokenize(q))
        hits = []
        for item in self._items:
            iws = self.tokenize(" ".join(self._get_strings(item)))
            # Earlier words are worth more
            is_iws = enumerate(iws, 1)
            # Sum the inverse of each index, for all words that match
            score = sum(1/i for (i, iw) in is_iws if self.match(qws, iw))
            if score:
                hits.append((score, item))
        # Higher-scoring hits first
        return sorted(hits, key=lambda score_item: score_item[0], reverse=True)

    def match(self, qws, iw):
        return any(iw.lower().startswith(qw.lower()) for qw in qws)
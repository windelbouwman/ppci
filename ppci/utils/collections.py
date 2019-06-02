""" Module with additional collection types.

- OrderedSet: A set like type which retains ordering.

Which are not included in the
standard library.

Inspiration:
http://code.activestate.com/recipes/576694/
"""

from collections.abc import MutableSet
from collections import OrderedDict


class OrderedSet(MutableSet):
    """ Set which retains order of elements """

    def __init__(self, iterable=None):
        end = []
        end += [None, end, end]
        self._end = end
        self._map = {}  # key -> [key, prev, next]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self._map)

    def __contains__(self, key):
        return key in self._map

    def add(self, value):
        if value not in self._map:
            end = self._end
            curr = end[1]
            curr[2] = end[1] = self._map[value] = [value, curr, end]

    def discard(self, value):
        """ Remove element from set """
        if value in self._map:
            value, prev_item, next_item = self._map.pop(value)
            prev_item[2] = next_item
            next_item[1] = prev_item

    def __getitem__(self, index):
        """ O(n) implementation for lookups """
        for i, key in enumerate(self):
            if i == index:
                return key

    def __iter__(self):
        end = self._end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self._end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, list(self))


__all__ = ("OrderedSet", "OrderedDict")


if __name__ == "__main__":
    s = OrderedSet("abracadabra")
    t = OrderedSet("simsalabim")
    print(s | t)
    print(s & t)
    print(s - t)

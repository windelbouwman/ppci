""" Module with additional collection types.

- OrderedSet: A set like type which retains ordering.

Which are not included in the
standard library.

Inspiration:
http://code.activestate.com/recipes/576694/
"""

from collections import MutableSet, OrderedDict


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

    def add(self, key):
        if key not in self._map:
            end = self._end
            curr = end[1]
            curr[2] = end[1] = self._map[key] = [key, curr, end]

    def discard(self, key):
        """ Remove element from set """
        if key in self._map:
            key, prev, next = self._map.pop(key)
            prev[2] = next
            next[1] = prev

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
        return '%s(%r)' % (self.__class__.__name__, list(self))


__all__ = ('OrderedSet', 'OrderedDict')


if __name__ == '__main__':
    s = OrderedSet('abracadabra')
    t = OrderedSet('simsalabim')
    print(s | t)
    print(s & t)
    print(s - t)

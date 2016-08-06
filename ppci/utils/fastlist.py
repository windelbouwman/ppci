"""
    Implementation of a list with faster index method.
"""


class FastList:
    """
        List drop-in replacement that supports cached index operation.
        So the first time the index is complexity O(n), the second time
        O(1). When the list is modified, the cache is cleared.
    """
    __slots__ = ['_items', '_index_map']

    def __init__(self):
        self._items = []
        self._index_map = {}

    def __iter__(self):
        return self._items.__iter__()

    def __len__(self):
        return self._items.__len__()

    def __getitem__(self, key):
        return self._items.__getitem__(key)

    def append(self, i):
        """ Append an item """
        self._index_map.clear()
        self._items.append(i)

    def insert(self, pos, i):
        """ Insert an item """
        self._index_map.clear()
        self._items.insert(pos, i)

    def remove(self, i):
        self._index_map.clear()
        self._items.remove(i)

    def index(self, i):
        """ Second time the lookup of index is done in O(1) """
        if i not in self._index_map:
            self._index_map[i] = self._items.index(i)
        return self._index_map[i]

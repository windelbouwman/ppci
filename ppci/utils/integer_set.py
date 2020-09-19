""" RangeSet / IntegerSet implementation.

An integer set is super handy, since we can store large
ranges of inetegers as simple intervals. Note that
this datatype is handy when we are dealing with
sets of integer ranges. When the set contains
integers that are sparse, do not use this.

Taken from:

https://github.com/MichaelPaddon/epsilon

"""

import bisect


class IntegerSet:
    """A container for sets of integers."""

    def __init__(self, *values):
        # Create intervals:
        ranges = []
        for value in values:
            if isinstance(value, int):
                ranges.append((value, value))
            elif isinstance(value, tuple):
                ranges.append((int(value[0]), int(value[1])))
            else:
                raise TypeError("Expected int or tuple")

        # Sort intervals:
        ranges = sorted(filter(lambda r: r[0] <= r[1], ranges))

        # Eliminate overlapping ranges:
        ranges = tuple(merge_overlapping_intervals(ranges))
        self.ranges = ranges

    def __repr__(self):
        inner = ",".join("{}..{}".format(a, b) for a, b in self.ranges)
        return "{{{}}}".format(inner)

    def __len__(self):
        return self.cardinality()

    def __bool__(self):
        return bool(self.ranges)

    def empty(self):
        return not self.ranges

    def cardinality(self) -> int:
        """ Determine total amount of values in this set. """
        total = 0
        for r in self.ranges:
            total += r[1] - r[0] + 1
        return total

    def __iter__(self):
        for r in self.ranges:
            for x in range(r[0], r[1] + 1):
                yield x

    def __contains__(self, item):
        return self.contains(item)

    def contains(self, value) -> bool:
        # Find index in sorted ranges:
        index = bisect.bisect(self.ranges, (value,))
        # print("contains", value, index, self.ranges)
        return (
            index < len(self.ranges) and value == self.ranges[index][0]
        ) or (
            index > 0
            and self.ranges[index - 1][0] <= value <= self.ranges[index - 1][1]
        )

    def union(self, other):
        ranges = self.ranges + other.ranges
        return IntegerSet(*ranges)

    def __or__(self, other):
        return self.union(other)

    def intersection(self, other):
        # print("intersection", self.ranges, other.ranges)
        ranges = []

        i, j = iter(self.ranges), iter(other.ranges)
        r, s = next(i, None), next(j, None)

        while r and s:
            x = max(r[0], s[0])
            y = min(r[1], s[1])
            if x <= y:
                ranges.append((x, y))

            if r[1] <= y:
                r = next(i, None)

            if s[1] <= y:
                s = next(j, None)
        return IntegerSet(*ranges)

    def __and__(self, other):
        return self.intersection(other)

    def __eq__(self, other):
        if isinstance(other, IntegerSet):
            return self.ranges == other.ranges
        else:
            return False

    def __hash__(self):
        return hash(self.ranges)

    def difference(self, other):
        ranges = []
        i, j = iter(self.ranges), iter(other.ranges)
        r, s = next(i, None), next(j, None)
        while r:
            if s:
                # range s might punch a hole in range r
                if r[0] > s[1]:
                    # range s before range r, no hole
                    s = next(j, None)
                elif r[1] < s[0]:
                    # range s after range r, no hole
                    ranges.append(r)
                    r = next(i, None)
                else:
                    # Overlap!
                    if r[0] < s[0]:
                        ranges.append((r[0], s[0] - 1))

                    if r[1] > s[1]:
                        r = (s[1] + 1, r[1])
                        s = next(j, None)
                    else:
                        r = next(i, None)
            else:
                ranges.append(r)
                r = next(i, None)

        return IntegerSet(*ranges)

    def __sub__(self, other):
        return self.difference(other)

    def symmetric_difference(self, other):
        return (self - other) | (other - self)

    def __xor__(self, other):
        return self.symmetric_difference(other)


def merge_overlapping_intervals(ranges):
    if ranges:
        r = ranges[0]
        for s in ranges[1:]:
            if s[0] > r[1] + 1:
                # Found hole!
                yield r
                r = s
            else:
                # s overlaps with r, merge end values
                r = (r[0], max(r[1], s[1]))

        yield r

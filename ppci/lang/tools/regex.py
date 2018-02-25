
""" Regular expression routines.

Implement regular expressions using derivatives.

"""

import abc


class Regex(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def nu(self):
        """ Determine if this regex is nullable or not """
        raise NotImplementedError()

    @abc.abstractmethod
    def derivative(self, symbol):
        raise NotImplementedError()

    def __or__(self, other):
        return LogicalOr(self, other)

    def __and__(self, other):
        return LogicalAnd(self, other)

    def __add__(self, other):
        return Concatenation(self, other)


NULL = 0


class Epsilon(Regex):
    """ The empty string """
    def nu(self):
        return self

    def derivative(self, symbol):
        return NULL

    def __str__(self):
        return ''


EPSILON = Epsilon()


class Symbol(Regex):
    def __init__(self, symbol):
        self._symbol = symbol

    def nu(self):
        return NULL

    def derivative(self, symbol):
        if symbol == self._symbol:
            return EPSILON
        else:
            return NULL

    def __str__(self):
        return self._symbol


class Kleene(Regex):
    """ Kleene closure r* """
    def __init__(self, expr):
        self._expr = expr

    def nu(self):
        return Epsilon()

    def derivative(self, symbol):
        return self._expr.derivative(symbol) + self

    def __str__(self):
        return '{}*'.format(self._expr)


class Concatenation(Regex):
    """ Concatenate two regular expressions a . b """
    def __init__(self, lhs, rhs):
        self._lhs = lhs
        self._rhs = rhs

    def nu(self):
        return self._lhs.nu() & self._rhs.nu()

    def derivative(self, symbol):
        nu = self._lhs.nu()
        return LogicalOr(
            Concatenation(self._lhs.derivative(symbol), self._rhs),
            Concatenation(nu, self._rhs.derivative(symbol)))

    def __str__(self):
        return '{}{}'.format(self._lhs, self._rhs)


class LogicalOr(Regex):
    """ Alternation operator a | b """
    def __init__(self, lhs, rhs):
        self._lhs = lhs
        self._rhs = rhs

    def nu(self):
        return self._lhs.nu() | self._rhs.nu()

    def derivative(self, symbol):
        return self._lhs.derivative(symbol) | self._rhs.derivative(symbol)

    def __str__(self):
        return '({})|({})'.format(self._lhs, self._rhs)


class LogicalAnd(Regex):
    """ operator a & b """
    def __init__(self, lhs, rhs):
        self._lhs = lhs
        self._rhs = rhs

    def nu(self):
        return self._lhs.nu() & self._rhs.nu()

    def derivative(self, symbol):
        return self._lhs.derivative(symbol) & self._rhs.derivative(symbol)

    def __str__(self):
        return '({})&({})'.format(self._lhs, self._rhs)


ab = Symbol('a') + Symbol('b')

# TODO: work in progress
print(ab)
print(ab.derivative('a'))
print(ab.derivative('b'))
print(ab.derivative('a').derivative('b'))


def parse(r):
    """ Parse a regular expression """
    raise NotImplementedError()


def compile(r):
    parse(r)
    raise NotImplementedError()

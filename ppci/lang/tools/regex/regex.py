""" Regular expression descriptions """

import abc
from . import symbol_set


class Regex(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def nu(self):
        """ Determine if this regex is nullable or not """
        raise NotImplementedError()

    @abc.abstractmethod
    def derivative(self, symbol):
        raise NotImplementedError()

    def __or__(self, other):
        if not isinstance(other, Regex):
            raise TypeError('Expected Regex but got {}'.format(type(other)))
        return LogicalOr(self, other)

    def __and__(self, other):
        if not isinstance(other, Regex):
            raise TypeError('Expected Regex but got {}'.format(type(other)))
        return LogicalAnd(self, other)

    def __add__(self, other):
        if not isinstance(other, Regex):
            raise TypeError('Expected Regex but got {}'.format(type(other)))
        return Concatenation(self, other)


class Epsilon(Regex):
    """ The empty string """
    def nu(self):
        return self

    def derivative(self, symbol):
        return NULL

    def __str__(self):
        return ''


EPSILON = Epsilon()


class SymbolSet(Regex):
    """ Match a single symbol """
    def __init__(self, symbols):
        self._symbols = symbol_set.SymbolSet(symbols)

    def nu(self):
        return NULL

    def derivative(self, symbol):
        return EPSILON if symbol in self._symbols else NULL

    def __str__(self):
        return str(self._symbols)


NULL = SymbolSet([])


def Symbol(symbol):
    """ Special case of a set with one item """
    return SymbolSet([symbol])


class Kleene(Regex):
    """ Kleene closure modifier r* """
    def __init__(self, expr):
        if not isinstance(expr, Regex):
            raise TypeError('Expected Regex but got {}'.format(type(expr)))
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
        if not isinstance(lhs, Regex):
            raise TypeError('Expected Regex but got {}'.format(type(lhs)))
        self._lhs = lhs
        if not isinstance(rhs, Regex):
            raise TypeError('Expected Regex but got {}'.format(type(rhs)))
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
        if not isinstance(lhs, Regex):
            raise TypeError('Expected Regex but got {}'.format(type(lhs)))
        self._lhs = lhs
        if not isinstance(rhs, Regex):
            raise TypeError('Expected Regex but got {}'.format(type(rhs)))
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
        if not isinstance(lhs, Regex):
            raise TypeError('Expected Regex but got {}'.format(type(rhs)))
        self._lhs = lhs
        if not isinstance(rhs, Regex):
            raise TypeError('Expected Regex but got {}'.format(type(rhs)))
        self._rhs = rhs

    def nu(self):
        return self._lhs.nu() & self._rhs.nu()

    def derivative(self, symbol):
        return self._lhs.derivative(symbol) & self._rhs.derivative(symbol)

    def __str__(self):
        return '({})&({})'.format(self._lhs, self._rhs)

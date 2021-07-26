""" Regular expression descriptions """

import abc
import itertools
import functools
from ....utils.integer_set import IntegerSet


class Regex(abc.ABC):
    @abc.abstractmethod
    def nu(self):
        """ Determine if this regex is nullable or not """
        raise NotImplementedError()

    @abc.abstractmethod
    def derivative(self, symbol):
        raise NotImplementedError()

    @abc.abstractmethod
    def derivative_classes(self):
        raise NotImplementedError()

    def nullable(self) -> bool:
        nu = self.nu()
        return nu == EPSILON

    @abc.abstractmethod
    def orderby(self):
        raise NotImplementedError()

    @property
    def null(self):
        return NULL

    def __eq__(self, other):
        return self.orderby() == other.orderby()

    def __hash__(self):
        return hash(self.orderby())

    def __or__(self, other):
        if not isinstance(other, Regex):
            raise TypeError("Expected Regex but got {}".format(type(other)))
        return logical_or(self, other)

    def __and__(self, other):
        if not isinstance(other, Regex):
            raise TypeError("Expected Regex but got {}".format(type(other)))
        return logical_and(self, other)

    def __add__(self, other):
        if not isinstance(other, Regex):
            raise TypeError("Expected Regex but got {}".format(type(other)))

        return concatenate(self, other)

    def optional(self):
        """Return a new regex, which is this regex, or empty string.
        Equivalent to the ?-operator.
        """
        return self | EPSILON

    def kleene(self):
        """ Apply the *-operator to this regex. """
        return Kleene(self)


class Epsilon(Regex):
    """ The empty string """

    def nu(self):
        return self

    def derivative(self, symbol):
        return NULL

    def derivative_classes(self):
        return [SIGMA.symbols]

    def orderby(self):
        return self.__class__.__name__

    def __str__(self):
        return "eps"


EPSILON = Epsilon()


class SymbolSet(Regex):
    """ Match a symbol set """

    def __init__(self, symbols):
        self.symbols = IntegerSet(*symbols)

    def nu(self):
        return NULL

    def derivative(self, symbol):
        if isinstance(symbol, str):
            symbol = ord(symbol)

        if symbol in self.symbols:
            return EPSILON
        else:
            return NULL

    def derivative_classes(self):
        return [self.symbols, SIGMA.symbols - self.symbols]

    def orderby(self):
        return self.__class__.__name__, self.symbols

    def __str__(self):
        return str(self.symbols)


NULL = SymbolSet([])
SIGMA = SymbolSet([(0, 255)])  # ASCII for now.


def Symbol(symbol):
    """ Special case of a set with one item """
    if isinstance(symbol, str):
        symbol = ord(symbol)

    return SymbolSet([symbol])


class Kleene(Regex):
    """ Kleene closure modifier r* """

    def __init__(self, expr):
        if not isinstance(expr, Regex):
            raise TypeError("Expected Regex but got {}".format(type(expr)))
        self.expr = expr

    def nu(self):
        return Epsilon()

    def derivative(self, symbol):
        return self.expr.derivative(symbol) + self

    def derivative_classes(self):
        return self.expr.derivative_classes()

    def orderby(self):
        return self.__class__.__name__, self.expr

    def __str__(self):
        return "{}*".format(self.expr)


def concatenate(left, right):
    if left == NULL:
        return NULL

    if right == NULL:
        return NULL

    if left == EPSILON:
        return right

    if right == EPSILON:
        return left

    return Concatenation(left, right)


class Concatenation(Regex):
    """ Concatenate two regular expressions a . b """

    def __init__(self, lhs, rhs):
        if not isinstance(lhs, Regex):
            raise TypeError("Expected Regex but got {}".format(type(lhs)))

        if lhs == EPSILON:
            raise ValueError(
                "Concatenating epsilon to something else makes no sense."
            )

        self.lhs = lhs
        if not isinstance(rhs, Regex):
            raise TypeError("Expected Regex but got {}".format(type(rhs)))
        self.rhs = rhs

    def nu(self):
        return self.lhs.nu() & self.rhs.nu()

    def derivative(self, symbol):
        nu = self.lhs.nu()
        return logical_or(
            concatenate(self.lhs.derivative(symbol), self.rhs),
            concatenate(nu, self.rhs.derivative(symbol)),
        )

    def derivative_classes(self):
        if self.lhs.nullable():
            return product_intersections(
                self.lhs.derivative_classes(), self.rhs.derivative_classes()
            )
        else:
            return self.lhs.derivative_classes()

    def orderby(self):
        return self.__class__.__name__, self.lhs, self.rhs

    def __str__(self):
        return "{}{}".format(self.lhs, self.rhs)


def logical_or(left, right):
    """ Perform logical or, but in a smart way
    so that we only construct a logical or when we need to.

    This implements the weaker notion of RE equivalence.
    """
    if isinstance(left, SymbolSet) and isinstance(right, SymbolSet):
        return SymbolSet(left.symbols | right.symbols)

    if left == right:
        return left

    if left == NULL:
        return right

    if right == NULL:
        return left

    return LogicalOr(left, right)


class LogicalOr(Regex):
    """ Alternation operator a | b """

    def __init__(self, lhs, rhs):
        if not isinstance(lhs, Regex):
            raise TypeError("Expected Regex but got {}".format(type(lhs)))

        if not isinstance(rhs, Regex):
            raise TypeError("Expected Regex but got {}".format(type(rhs)))

        if lhs == rhs:
            raise ValueError("Logical or of the same values makes no sense")

        if lhs == NULL:
            raise ValueError("Cannot logical or with NULL")

        if rhs == NULL:
            raise ValueError("Cannot logical or with NULL")

        self.lhs = lhs
        self.rhs = rhs

    def nu(self):
        return self.lhs.nu() | self.rhs.nu()

    def derivative(self, symbol):
        return self.lhs.derivative(symbol) | self.rhs.derivative(symbol)

    def derivative_classes(self):
        return product_intersections(
            self.lhs.derivative_classes(), self.rhs.derivative_classes()
        )

    def orderby(self):
        return self.__class__.__name__, self.lhs, self.rhs

    def __str__(self):
        return "({})|({})".format(self.lhs, self.rhs)


def logical_and(lhs, rhs):
    if lhs == rhs:
        # We must match left and right,
        # but since this is equal, we must
        # match one of the two.
        return lhs

    if lhs == NULL:
        return lhs

    if rhs == NULL:
        return rhs

    return LogicalAnd(lhs, rhs)


class LogicalAnd(Regex):
    """ operator a & b """

    def __init__(self, lhs, rhs):
        if not isinstance(lhs, Regex):
            raise TypeError("Expected Regex but got {}".format(type(rhs)))

        if not isinstance(rhs, Regex):
            raise TypeError("Expected Regex but got {}".format(type(rhs)))

        if lhs == rhs:
            raise ValueError(
                "Logical and of two the same values makes no sense"
            )

        if lhs == NULL:
            raise ValueError("Cannot logical and with NULL")

        if rhs == NULL:
            raise ValueError("Cannot logical and with NULL")

        self.lhs = lhs
        self.rhs = rhs

    def nu(self):
        return self.lhs.nu() & self.rhs.nu()

    def derivative(self, symbol):
        return self.lhs.derivative(symbol) & self.rhs.derivative(symbol)

    def derivative_classes(self):
        return product_intersections(
            self.lhs.derivative_classes(), self.rhs.derivative_classes()
        )

    def orderby(self):
        return self.__class__.__name__, self.lhs, self.rhs

    def __str__(self):
        return "({})&({})".format(self.lhs, self.rhs)


def product_intersections(*sets):
    return list(
        filter(None, (a.intersection(b) for a, b in itertools.product(*sets)))
    )


class ExpressionVector:
    """ Holds a vector of name, expression pairs. """

    def __init__(self, vector):
        self.vector = tuple(vector)

    def __repr__(self):
        return "Vec: " + " $ ".join(map(str, self.vector))

    def __eq__(self, other):
        return self.vector == other.vector

    def __hash__(self):
        return hash(self.vector)

    def nullable(self):
        """ Return names of the expressions that are nullable. """
        return [name for name, expr in self.vector if expr.nullable()]

    @property
    def null(self):
        return ExpressionVector([(name, NULL) for name, _ in self.vector])

    def derivative_classes(self):
        return list(
            filter(
                None,
                functools.reduce(
                    product_intersections,
                    (expr.derivative_classes() for _, expr in self.vector),
                ),
            )
        )

    def derivative(self, symbol):
        return ExpressionVector(
            [(name, expr.derivative(symbol)) for name, expr in self.vector]
        )

""" Regular expression parsing.

This module is able to parse regular expressions.

"""

from . import regex


def parse(r):
    """ Parse a regular expression """
    parser = Parser()
    return parser.parse(r)


class Parser:
    """ Regular expression program parser """

    def parse(self, txt):
        self.txt = txt
        self.pos = 0
        if self.at_end():
            expr = regex.EPSILON
        else:
            expr = self._parse_top()
            while not self.at_end():
                expr2 = self._parse_top()
                expr = expr + expr2
        return expr

    def current(self):
        if self.pos < len(self.txt):
            return self.txt[self.pos]

    def at_end(self):
        return self.pos >= len(self.txt)

    def peek(self, c):
        """ Look at next character """
        return c == self.current()

    def _next_char(self):
        c = self.current()
        if c is None:
            raise ValueError("At end of string!")

        self.pos += 1
        return c

    def eat(self, c=None):
        """ Consume single character """
        actual = self._next_char()

        if c is None:
            # Handle escape backslash:
            if actual == "\\":
                actual = self._next_char()
            return actual
        elif actual == c:
            return actual
        else:
            raise ValueError("Expected {} but got {}".format(c, actual))

    def did_eat(self, c):
        if self.peek(c):
            self.eat(c)
            return True
        return False

    def _parse_top(self):
        return self._parse_or()

    def _parse_or(self):
        expr = self._parse_and()
        while self.did_eat("|"):
            rhs = self._parse_and()
            expr = expr | rhs
        return expr

    def _parse_and(self):
        return self._parse_element()

    def _parse_element(self):
        """ Parse single element of regex """
        if self.peek("("):
            self.eat("(")
            expr = self._parse_top()
            self.eat(")")
        elif self.peek("["):
            expr = self._parse_set()
        elif self.peek("."):
            self.eat(".")
            expr = regex.SIGMA
        else:
            expr = self._parse_symbol()

        expr = self._parse_modifier(expr)

        return expr

    def _parse_symbol(self):
        """ Simple symbol. """
        sym = self.eat()
        return regex.Symbol(sym)

    def _parse_set(self):
        """ Parse a set of options '[0-9abc]' """
        self.eat("[")
        ranges = []
        # Check inversion:
        if self.peek("^"):
            self.eat("^")
            complement = True
        else:
            complement = False

        # options.append(complement)
        while not self.peek("]"):
            start = ord(self.eat())
            if self.peek("-"):
                self.eat("-")
                end = ord(self.eat())
                if not (start < end):
                    raise ValueError("Start must be before end")
                ranges.append((start, end))
            else:
                ranges.append(start)
        self.eat("]")

        if not ranges:
            raise ValueError(
                "Expected at least 1 item in regex option group [...]"
            )

        expr = regex.SymbolSet(ranges)

        if complement:
            expr = not expr
            raise NotImplementedError("TODO?")
            # Something like this: expr = SIGMA - expr?

        return expr

    def _parse_modifier(self, expr):
        """ Parse any modifiers after an expression """
        if self.did_eat("*"):
            expr = regex.Kleene(expr)
        elif self.did_eat("+"):
            expr = expr + regex.Kleene(expr)
        elif self.did_eat("?"):
            expr = expr | regex.EPSILON

        return expr

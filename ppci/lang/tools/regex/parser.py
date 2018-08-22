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
        expr = self._parse_top()
        return expr

    def current(self):
        if self.pos < len(self.txt):
            return self.txt[self.pos]

    def peek(self, c):
        """ Look at next character """
        return c == self.current()

    def eat(self, c=None):
        """ Consume single character """
        actual = self.current()
        if actual is None:
            raise ValueError('At end of string!')

        self.pos += 1
        if c is None:
            return actual
        elif actual == c:
            return actual
        else:
            raise ValueError('Expected {} but got {}'.format(c, actual))

    def did_eat(self, c):
        if self.peek(c):
            self.eat(c)
            return True
        return False

    def _parse_top(self):
        return self._parse_or()

    def _parse_or(self):
        expr = self._parse_and()
        while self.did_eat('|'):
            rhs = self._parse_and()
            expr = expr | rhs

    def _parse_and(self):
        return self._parse_element()

    def _parse_element(self):
        """ Parse single element of regex """
        if self.peek('('):
            self.eat('(')
            expr = self._parse_top()
            self.eat(')')
        elif self.peek('['):
            return self._parse_set()
        else:
            raise NotImplementedError()
            expr = self._parse_set()
        return expr

    def _parse_set(self):
        """ Parse a set of options '[0-9abc]' """
        self.eat('[')
        options = []
        # Check inversion:
        if self.peek('^'):
            self.eat('^')
            complement = True
        else:
            complement = False

        options.append(complement)
        while not self.peek(']'):
            start = self.eat()
            if self.peek('-'):
                self.eat('-')
                end = self.eat()
                options.append((start, end))
            else:
                options.append(start)
        self.eat(']')

    def _parse_modifier(self, expr):
        """ Parse any modifiers after an expression """
        if self.eat('*'):
            return regex.Kleene(expr)
        elif self.eat('+'):
            return expr + regex.Kleene(expr)
        elif self.eat('?'):
            raise NotImplementedError()
            # return expr | eps
        else:
            return expr

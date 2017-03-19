import os
import logging
import operator

from ...common import CompilerError, Token
from .lexer import Lexer


class CPreProcessor:
    """ A pre-processor for C source code """
    logger = logging.getLogger('preprocessor')

    def __init__(self):
        self.defines = {}
        self.include_directories = []

        # TODO: temporal default paths:
        self.add_include_path('/usr/include')
        self.add_include_path(
            '/usr/lib/gcc/x86_64-pc-linux-gnu/6.3.1/include/')

    def process(self, f, filename=None):
        """ Process the given open file into tokens """
        self.logger.debug('Processing %s', filename)
        clexer = Lexer()
        tokens = clexer.lex(f, filename)
        macro_expander = Expander(self)
        for token in macro_expander.process(tokens):
            yield token

    def add_include_path(self, path):
        self.include_directories.append(path)

    def define(self, name, value):
        """ Register a define """
        self.defines[name] = value

    def undefine(self, name):
        """ Kill a define! """
        if self.is_defined(name):
            self.defines.pop(name)

    def is_defined(self, name):
        """ Check if the given define is defined. """
        return name in self.defines

    def get_define(self, name):
        """ Retrieve the given define! """
        return self.defines[name]

    def include(self, filename):
        """ Include the given filename into the current output """
        for path in self.include_directories:
            full_path = os.path.join(path, filename)
            if os.path.exists(full_path):
                self.logger.debug('Including %s', full_path)
                with open(full_path, 'r') as f:
                    for token in self.process(f, full_path):
                        yield token
                return
        self.logger.error('File not found: %s', filename)
        raise FileNotFoundError(filename)


class Expander:
    """ Per source or header file an expander class is created """
    logger = logging.getLogger('preprocessor')

    def __init__(self, context):
        self.context = context
        self.if_stack = []
        self.enabled = True

        # A black list of defines currently being expanded:
        self.blue_list = set()

    def process(self, tokens):
        """ Process a token sequence into another token sequence.

        This function returns an iterator that must be looped over.
        """
        self.tokens = tokens
        self.next_token()
        return self.process_normal()

    @property
    def peak(self):
        if self.token:
            return self.token.typ

    def next_token(self):
        self.token = next(self.tokens, None)

    def consume(self, typ=None, skip_space=False):
        if skip_space:
            self.skip_space()

        if not typ:
            typ = self.token.typ

        if self.token.typ != typ:
            self.error('Expected {} but got {}'.format(typ, self.token.typ))

        t = self.token
        self.next_token()
        return t

    def error(self, msg):
        if self.token:
            raise CompilerError(msg, self.token.loc)
        else:
            raise CompilerError(msg)

    def skip_space(self):
        while self.peak == 'WS':
            self.next_token()

    def skip_to_eol(self):
        while self.peak != 'BOL':
            self.next_token()

    def process_normal(self):
        """ Iterator of processed tokens """
        while self.peak:
            # TODO: assert beginning of line?
            if self.peak == '#':
                # We are inside a directive!
                self.consume('#')
                directive = self.consume('ID', skip_space=True).val
                for subtoken in self.handle_directive(directive):
                    yield subtoken

                # Ensure end of line!
                self.skip_space()
                yield self.consume('BOL')
            else:
                # This is not a directive, but normal text:
                token = self.consume()
                if self.enabled:
                    for subtoken in self.expand(token):
                        yield subtoken

        if self.if_stack:
            self.error('#if not properly closed')

    def expand_all(self, tokens):
        for token in tokens:
            for subtoken in self.expand(token):
                yield subtoken

    def expand(self, token):
        """ Expand a single token into possibly more tokens! """
        if token.typ == 'ID':
            name = token.val
            if self.context.is_defined(name) and name not in self.blue_list:
                self.blue_list.add(name)
                for subtoken in self.expand_all(self.context.get_define(name)):
                    yield subtoken
                self.blue_list.remove(name)
            else:
                yield token
        else:
            yield token

    def expr_grab(self):
        pass

    def expr_expand(self):
        """ Grab tokens for an expression until end of line """
        while not self.peak == 'BOL':
            token = self.consume(skip_space=True)
            if token.typ == 'ID':
                name = token.val
                if name == 'defined':
                    parenthesis = self.peak == '('
                    if parenthesis:
                        self.consume('(', skip_space=True)
                    d = self.consume('ID', skip_space=True).val
                    value = int(self.context.is_defined(d))
                    yield Token('NUMBER', value, token.loc)
                    if parenthesis:
                        self.consume(')', skip_space=True)
                else:
                    for subtoken in self.expand(token):
                        yield subtoken
            else:
                yield token

    def eval_expr(self):
        """ Evaluate an expression """
        return ExpressionParser(self.context, self.expr_expand()).parse()

    def handle_directive(self, directive):
        """ Handle a single preprocessing directive """

        if directive == 'ifdef':
            if self.enabled:
                self.consume('WS')
                test_define = self.consume('ID', skip_space=True).val
                condition = self.context.is_defined(test_define)
                self.if_stack.append(IfState(condition))
            else:
                self.skip_to_eol()
                self.if_stack.append(IfState(True))
            self.calculate_active()
        elif directive == 'if':
            if self.enabled:
                self.consume('WS')
                condition = bool(self.eval_expr())
                self.if_stack.append(IfState(condition))
            else:
                self.skip_to_eol()
                self.if_stack.append(IfState(True))
            self.calculate_active()
        elif directive == 'elif':
            if not self.if_stack:
                self.error('#elif outside #if')
            if self.if_stack[-1].in_else:
                self.error('#elif after #else')
            if self.enabled:
                self.consume('WS')
                condition = bool(self.eval_expr())
                self.if_stack[-1].condition = condition
            else:
                self.skip_to_eol()
            self.calculate_active()
        elif directive == 'else':
            if self.if_stack[-1].in_else:
                self.error('One else too much in #ifdef')
            self.if_stack[-1].in_else = True
            self.calculate_active()
        elif directive == 'ifndef':
            if self.enabled:
                test_define = self.consume('ID', skip_space=True).val
                condition = not self.context.is_defined(test_define)
                self.if_stack.append(IfState(condition))
            else:
                self.skip_to_eol()
                self.if_stack.append(IfState(True))
            self.calculate_active()
        elif directive == 'endif':
            if not self.if_stack:
                self.error('Mismatching #endif')
            self.if_stack.pop(-1)
            self.calculate_active()
        elif directive == 'include':
            if self.enabled:
                self.consume('WS')
                if self.peak == '<':
                    # TODO: this is a bad way of getting the filename:
                    filename = ''
                    self.consume('<')
                    while self.peak != '>':
                        filename += self.consume().val
                    self.consume('>')
                    include_filename = filename
                else:
                    include_filename = self.consume('STRING').val[1:-1]

                for token in self.context.include(include_filename):
                    yield token
            else:
                self.skip_to_eol()
        elif directive == 'define':
            if self.enabled:
                name = self.consume('ID', skip_space=True).val
                if self.peak == 'BOL':
                    # Hmm, '#define X', set it to 1!
                    value = [Token('NUMBER', 1, self.token.loc)]
                    self.context.define(name, value)
                else:
                    if self.peak == '(':
                        # Function like macro!
                        self.consume('(', skip_space=True)
                        args = []
                        self.skip_space()
                        if self.peak == ')':
                            self.consume(')', skip_space=True)
                        else:
                            args.append(self.consume('ID'))
                            self.skip_space()
                            while self.peak == ',':
                                self.consume(',')
                                args.append(
                                    self.consume('ID', skip_space=True))
                                self.skip_space()
                            self.consume(')', skip_space=True)
                    self.consume('WS')
                    value = self.parse_macro()
                    self.context.define(name, value)
            else:
                self.skip_to_eol()
        elif directive == 'undef':
            if self.enabled:
                name = self.consume('ID', skip_space=True).val
                self.context.undefine(name)
            else:
                self.skip_to_eol()
        else:
            if self.enabled:
                self.logger.error('todo: %s', directive)
                raise NotImplementedError(directive)
            else:
                self.skip_to_eol()

    def calculate_active(self):
        """ Determine if we may emit code given the current if-stack """
        if self.if_stack:
            self.enabled = all(i.may_encode() for i in self.if_stack)
        else:
            self.enabled = True

    def parse_macro(self):
        expr = []
        while not self.peak == 'BOL':
            expr.append(self.consume())
        return expr


class Macro:
    def __init__(self, name):
        self.name = name


class FunctionMacro(Macro):
    def __init__(self, name, args):
        pass


class ExpressionParser:
    """ Simple expression parser for preprocessor expressions """
    logger = logging.getLogger('ppexpr')

    def __init__(self, context, tokens):
        self.context = context
        self.tokens = tokens
        self.next_token()

    def next_token(self):
        self.token = next(self.tokens, None)

    def consume(self, typ=None):
        if not typ:
            typ = self.token.typ

        if self.token.typ != typ:
            self.error('Expected {} but got {}'.format(typ, self.token.typ))

        t = self.token
        self.next_token()
        return t

    def error(self, msg):
        if self.token:
            raise CompilerError(msg, self.token.loc)
        else:
            raise CompilerError(msg)

    @property
    def peak(self):
        if self.token:
            return self.token.typ

    def parse(self):
        expr = self.parse_expression()
        if self.peak is not None:
            self.error('Error in expression!')
        return expr

    def parse_expression(self, priority=0):
        """ Parse an expression in an #if

        Idea taken from: https://github.com/shevek/jcpp/blob/master/
            src/main/java/org/anarres/cpp/Preprocessor.java
        """
        if self.peak == '!':
            self.consume('!')
            lhs = int(not(bool(self.parse_expression(11))))
        elif self.peak == '(':
            self.consume('(')
            lhs = self.parse_expression(0)
            self.consume(')')
        elif self.peak == 'ID':
            name = self.consume('ID').val
            self.logger.warning('Attention: undefined "%s"', name)
            lhs = 0
        elif self.peak == 'NUMBER':
            value = self.consume('NUMBER').val
            lhs = int(value)
        else:
            raise NotImplementedError(self.peak)

        op_map = {
            '+': (10, operator.add),
            '-': (10, operator.sub),
            '*': (11, operator.mul),
            '/': (11, operator.floordiv),
            '%': (11, operator.mod),
            '<': (8, lambda x, y: int(x < y)),
            '>': (8, lambda x, y: int(x > y)),
            '<=': (8, lambda x, y: int(x <= y)),
            '>=': (8, lambda x, y: int(x >= y)),
            '==': (7, lambda x, y: int(x == y)),
            '!=': (7, lambda x, y: int(x != y)),
            '&': (6, operator.and_),
            '^': (5, operator.xor),
            '|': (4, operator.or_),
            '&&': (3, lambda x, y: int(x and y)),
            '||': (2, lambda x, y: int(x or y)),
        }

        while True:
            # This would be the next operator:
            op = self.peak

            # Determine if the operator has a low enough priority:
            pri = op_map[op][0] if op in op_map else None
            if (pri is None) or (pri <= priority):
                break

            # We are go, eat the operator and the rhs (right hand side)
            self.consume(op)
            rhs = self.parse_expression(pri)

            if op in op_map:
                lhs = op_map[op][1](lhs, rhs)
            else:
                raise NotImplementedError(op)

        # print('lhs=', lhs)
        return lhs


class IfState:
    """ If status for use on the if-stack """
    def __init__(self, condition):
        self.condition = condition
        self.in_else = False  # Indicator whether we are in the else clause.

    def may_encode(self):
        """ Determine given whether we are active according to this state """
        if self.in_else:
            return not self.condition
        else:
            return self.condition


class CTokenPrinter:
    """ Printer that can turn a preprocessed stream of tokens into text """
    def dump(self, tokens, file=None):
        for token in tokens:
            # print(token)
            print(token.val, end='', file=file)


def skip_ws(tokens):
    """ Strip out whitespace tokens from a given token series """
    for token in tokens:
        if token.typ in ['BOL', 'WS']:
            pass
        else:
            yield token


def prepare_for_parsing(tokens):
    """ Strip out tokens on the way from preprocessor to parser.

    Apply several modifications on the token stream to adapt it
    to the format that the parser requires.

    This involves:
    - Removal of whitespace
    """
    keywords = ['true', 'false',
                'else', 'if', 'while', 'for', 'return',
                'struct', 'enum',
                'typedef', 'static', 'const',
                'int', 'void', 'char', 'float', 'double']

    for token in skip_ws(tokens):
        if token.typ == 'ID':
            if token.val in keywords:
                token.typ = token.val
            yield token
        else:
            yield token

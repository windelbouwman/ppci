""" C preprocessor.

This file contains an implementation of the C preprocessor. Since the
preprocessor is working line for line, the data structure of choice is
a list of tokens per line. Each token also has info about the amount
of whitespace preceeding the token.

Sourcecode of inspiration:

- https://github.com/shevek/jcpp/blob/master/src/main/java/org/anarres/cpp/
  Preprocessor.java
- https://github.com/drh/lcc/blob/master/cpp/macro.c
"""

import os
import logging
import operator

from ...common import CompilerError
from .lexer import Lexer, CToken


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
        """ Process the given open file into expanded lines of tokens """
        self.logger.debug('Processing %s', filename)
        clexer = Lexer()
        lines = clexer.lex(f, filename)
        macro_expander = Expander(self)
        for line in macro_expander.process(lines):
            yield line

    def add_include_path(self, path):
        self.include_directories.append(path)

    def define(self, macro):
        """ Register a define """
        if self.is_defined(macro.name):
            raise CompilerError('Cannot redefine {}'.format(macro.name))
        self.defines[macro.name] = macro

    def undefine(self, name: str):
        """ Kill a define! """
        if self.is_defined(name):
            self.defines.pop(name)

    def is_defined(self, name: str) -> bool:
        """ Check if the given define is defined. """
        return name in self.defines

    def get_define(self, name: str):
        """ Retrieve the given define! """
        return self.defines[name]

    def include(self, filename):
        """ Turn the given filename into a series of lines """
        for path in self.include_directories:
            full_path = os.path.join(path, filename)
            if os.path.exists(full_path):
                self.logger.debug('Including %s', full_path)
                with open(full_path, 'r') as f:
                    for line in self.process(f, full_path):
                        yield line
                return
        self.logger.error('File not found: %s', filename)
        raise FileNotFoundError(filename)


class LineEater:
    """ This class processes tokens in a line and keeps track of position """
    logger = logging.getLogger('preprocessor')

    def __init__(self, line):
        self.tokens = iter(line)
        self.token = None
        self.next_token()

    @property
    def peak(self):
        if self.token:
            return self.token.typ

    @property
    def at_end(self):
        return self.token is None

    def next_token(self):
        t = self.token
        self.token = next(self.tokens, None)
        return t

    def consume(self, typ=None):
        if not typ:
            typ = self.token.typ

        if self.token.typ != typ:
            self.error('Expected {} but got {}'.format(typ, self.token.typ))

        return self.next_token()

    def has_consumed(self, typ):
        if self.peak == typ:
            self.consume(typ)
            return True
        return False

    def eat_line(self):
        while not self.at_end:
            self.next_token()

    def error(self, msg):
        if self.token:
            raise CompilerError(msg, self.token.loc)
        else:
            raise CompilerError(msg)

    def warning(self, msg):
        self.logger.warning(msg)


class Expander:
    """ Per source or header file an expander class is created

    Contains:
    - An if-stack to keep track of if-else nesting levels
    """
    logger = logging.getLogger('preprocessor')

    def __init__(self, context):
        super().__init__()
        self.context = context
        self.if_stack = []
        self.enabled = True

        # A black list of defines currently being expanded:
        self.blue_list = set()

    def process(self, lines):
        """ Process a line sequence into a token sequence.

        This function returns an token-line iterator that must be looped over.
        """
        for line in lines:
            le = LineEater(line)
            if le.has_consumed('#'):
                # We are inside a directive!
                for line in self.handle_directive(le):
                    yield line

                # Ensure end of line!
                if le.peak is not None:
                    le.error('Expected end of line')
            else:
                # This is not a directive, but normal text:
                if self.enabled:
                    yield self.expand_line(le)

        if self.if_stack:
            le.error('#if not properly closed')

    def expand_line(self, le, expression_expansion=False):
        """ Expand a token-line into a macro-expanded token-line """
        new_line = []
        while not le.at_end:
            if le.peak == 'ID':
                identifier = le.consume('ID')
                if identifier.val == 'defined' and expression_expansion:
                    if le.has_consumed('('):
                        name = le.consume('ID')
                        le.consume(')')
                    else:
                        name = le.consume('ID')
                    value = int(self.context.is_defined(name.val))
                    new_line.append(
                        CToken('NUMBER', value, ' ', identifier.loc))
                else:
                    for subtoken in self.expand(identifier, le):
                        new_line.append(subtoken)
            else:
                new_line.append(le.consume())
        return new_line

    def expand(self, token, le):
        """ Expand a single token into possibly more tokens! """
        name = token.val
        if self.context.is_defined(name) and name not in self.blue_list:
            self.blue_list.add(name)
            macro = self.context.get_define(name)
            if macro.args is None:
                # Macro without arguments
                mle = LineEater(macro.value)
            else:
                # This macro requires arguments
                args = self.gatherargs(le)
                if len(args) != len(macro.args):
                    le.error(
                        'Got {} arguments, but expected {}'.format(
                            len(args), len(macro.args)))

                subst_m = self.substitute_arguments(macro, args)
                mle = LineEater(subst_m)

            # Handle token concatenate here?
            line3 = self.concatenate(mle)
            mle = LineEater(line3)

            # Expand macro line:
            for subtoken in self.expand_line(mle):
                yield subtoken
            self.blue_list.remove(name)
        else:
            yield token

    def gatherargs(self, le):
        """ Collect expanded arguments for macro """
        args = []
        le.consume('(')
        while True:
            arg = []
            while le.peak not in (')', ','):
                arg.append(le.consume())
            a2 = self.expand_line(LineEater(arg))
            args.append(a2)
            if le.has_consumed(')'):
                break
            le.consume(',')
        return args

    def substitute_arguments(self, macro, args):
        """ Return macro contents with substituted arguments.

        Pay special care to # and ## operators """
        new_line = []
        repl_map = {fp.val: a for fp, a in zip(macro.args, args)}
        self.logger.debug('replacement map: %s', repl_map)
        sle = LineEater(macro.value)
        while not sle.at_end:
            if sle.has_consumed('#'):
                # Stringify operator '#'!
                arg_name = sle.consume('ID')
                if arg_name.val in repl_map:
                    new_line.append(self.stringify(
                        repl_map[arg_name.val], arg_name.loc))
                else:
                    sle.error(
                        '{} does not refer a macro argument'.format(
                            arg_name.val))
            else:
                if sle.peak == 'ID' and sle.token.val in repl_map:
                    token = sle.consume('ID')
                    new_line.extend(repl_map[token.val])
                else:
                    token = sle.consume()
                    new_line.append(token)
        return new_line

    def stringify(self, snippet, loc):
        """ Handle the '#' stringify operator """
        string_value = '"{}"'.format(''.join(map(str, snippet)))
        return CToken('STRING', string_value, '', loc)

    def concatenate(self, le):
        """ Handle the '##' token concatenation operator """
        glue_line = []
        while not le.at_end:
            if le.peak == 'ID':
                lhs = le.consume('ID')
                while le.has_consumed('##'):
                    if le.peak == 'ID':
                        rhs = le.consume('ID').val
                    else:
                        le.error('Cannot glue {}'.format(le.peak))
                    lhs = CToken('ID', lhs.val + rhs, lhs.space, lhs.loc)
                glue_line.append(lhs)
            else:
                glue_line.append(le.consume())
        return glue_line

    def handle_directive(self, le):
        """ Handle a single preprocessing directive """
        directive = le.consume('ID').val
        if directive == 'ifdef':
            if self.enabled:
                test_define = le.consume('ID').val
                condition = self.context.is_defined(test_define)
                self.if_stack.append(IfState(condition))
            else:
                le.eat_line()
                self.if_stack.append(IfState(True))

            self.calculate_active()
        elif directive == 'if':
            if self.enabled:
                condition = bool(self.eval_expr(le))
                self.if_stack.append(IfState(condition))
            else:
                le.eat_line()
                self.if_stack.append(IfState(True))
            self.calculate_active()
        elif directive == 'elif':
            if not self.if_stack:
                le.error('#elif outside #if')

            if self.if_stack[-1].in_else:
                le.error('#elif after #else')

            if self.enabled:
                condition = bool(self.eval_expr(le))
                self.if_stack[-1].condition = condition
            else:
                le.eat_line()

            self.calculate_active()
        elif directive == 'else':
            if not self.if_stack:
                self.error('#else outside #if')

            if self.if_stack[-1].in_else:
                self.error('One else too much in #ifdef')

            self.if_stack[-1].in_else = True
            self.calculate_active()
        elif directive == 'ifndef':
            if self.enabled:
                test_define = le.consume('ID').val
                condition = not self.context.is_defined(test_define)
                self.if_stack.append(IfState(condition))
            else:
                le.eat_line()
                self.if_stack.append(IfState(True))

            self.calculate_active()
        elif directive == 'endif':
            if not self.if_stack:
                self.error('Mismatching #endif')
            self.if_stack.pop(-1)
            self.calculate_active()
        elif directive == 'include':
            if self.enabled:
                if le.peak == '<':
                    # TODO: this is a bad way of getting the filename:
                    filename = ''
                    le.consume('<')
                    while le.peak != '>':
                        filename += le.consume().val
                    le.consume('>')
                    include_filename = filename
                else:
                    include_filename = le.consume('STRING').val[1:-1]

                for line in self.context.include(include_filename):
                    yield line
            else:
                le.eat_line()
        elif directive == 'define':
            if self.enabled:
                name = le.consume('ID')
                if le.peak is None:
                    # Hmm, '#define X', set it to 1!
                    value = [CToken('NUMBER', 1, ' ', name.loc)]
                    macro = Macro(name.val, None, value)
                else:
                    if le.peak == '(' and not le.token.space:
                        # Function like macro!
                        le.consume('(')
                        args = []
                        if le.peak == ')':
                            le.consume(')')
                        else:
                            args.append(le.consume('ID'))
                            while le.has_consumed(','):
                                args.append(
                                    le.consume('ID'))
                            le.consume(')')
                    else:
                        args = None
                    value = []
                    while le.peak:
                        value.append(le.consume())
                    macro = Macro(name.val, args, value)
                self.context.define(macro)
            else:
                le.eat_line()
        elif directive == 'undef':
            if self.enabled:
                name = le.consume('ID').val
                self.context.undefine(name)
            else:
                le.eat_line()
        elif directive == 'error':
            if self.enabled:
                msg = le.consume('STRING')
                le.error(msg)
            else:
                le.eat_line()
        elif directive == 'warning':
            if self.enabled:
                msg = le.consume('STRING')
                le.warning(msg)
            else:
                le.eat_line()
        else:
            self.logger.error('todo: %s', directive)
            raise NotImplementedError(directive)
        yield []

    def calculate_active(self):
        """ Determine if we may emit code given the current if-stack """
        if self.if_stack:
            self.enabled = all(i.may_encode for i in self.if_stack)
        else:
            self.enabled = True

    def eval_expr(self, le):
        """ Evaluate an expression """
        # Grab expression till end of line
        condition_line = []
        while not le.at_end:
            condition_line.append(le.consume())

        # Expand macros:
        cle = LineEater(condition_line)
        condition = self.expand_line(cle, expression_expansion=True)

        # And evaluate:
        le2 = LineEater(condition)
        return self.parse_expression(le2)

    def parse_expression(self, le, priority=0):
        """ Parse an expression in an #if

        Idea taken from: https://github.com/shevek/jcpp/blob/master/
            src/main/java/org/anarres/cpp/Preprocessor.java
        """
        if le.has_consumed('!'):
            lhs = int(not(bool(self.parse_expression(le, 11))))
        elif le.has_consumed('('):
            lhs = self.parse_expression(le, 0)
            le.consume(')')
        elif le.peak == 'ID':
            name = le.consume('ID').val
            self.logger.warning('Attention: undefined "%s"', name)
            lhs = 0
        elif le.peak == 'NUMBER':
            value = le.consume('NUMBER').val
            lhs = cnum(value)
        else:
            raise NotImplementedError(le.peak)

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
            op = le.peak

            # Determine if the operator has a low enough priority:
            pri = op_map[op][0] if op in op_map else None
            if (pri is None) or (pri <= priority):
                break

            # We are go, eat the operator and the rhs (right hand side)
            le.consume(op)
            rhs = self.parse_expression(le, pri)

            if op in op_map:
                lhs = op_map[op][1](lhs, rhs)
            else:
                raise NotImplementedError(op)

        return lhs


def cnum(txt):
    """ Convert C number to integer """
    if isinstance(txt, int):
        return txt
    if txt.endswith('L'):
        return int(txt[:-1])
    else:
        return int(txt)


class Macro:
    """ Macro define """
    def __init__(self, name, args, value):
        self.name = name
        self.args = args
        self.value = value


class IfState:
    """ If status for use on the if-stack """
    def __init__(self, condition):
        self.condition = condition
        self.in_else = False  # Indicator whether we are in the else clause.

    @property
    def may_encode(self):
        """ Determine given whether we are active according to this state """
        if self.in_else:
            return not self.condition
        else:
            return self.condition


class CTokenPrinter:
    """ Printer that can turn a stream of token-lines into text """
    def dump(self, lines, file=None):
        for line in lines:
            # print(line)
            text = ''.join(map(str, line))
            print(text, file=file)


def lines_to_tokens(lines):
    """ Generate a stream of tokens from lines of tokens """
    for line in lines:
        for token in line:
            yield token


def prepare_for_parsing(lines):
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

    for token in lines_to_tokens(lines):
        if token.typ == 'ID':
            if token.val in keywords:
                token.typ = token.val
            yield token
        else:
            yield token

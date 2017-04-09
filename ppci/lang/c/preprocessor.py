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
from .lexer import CLexer, CToken


class CPreProcessor:
    """ A pre-processor for C source code """
    logger = logging.getLogger('preprocessor')

    def __init__(self, coptions):
        self.coptions = coptions
        self.defines = {}
        self.include_directories = []

        # TODO: temporal default paths:
        self.add_include_path('/usr/include')
        self.add_include_path(
            '/usr/lib/gcc/x86_64-pc-linux-gnu/6.3.1/include/')

    def process(self, f, filename=None):
        """ Process the given open file into expanded lines of tokens """
        self.logger.debug('Processing %s', filename)
        clexer = CLexer(self.coptions)
        tokens = clexer.lex(f, filename)
        macro_expander = Expander(self)
        for token in macro_expander.process(tokens):
            yield token

    def add_include_path(self, path):
        """ Add a path to the list of include paths """
        self.include_directories.append(path)

    def define(self, macro):
        """ Register a define """
        if self.is_defined(macro.name):
            if self.get_define(macro.name).protected:
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
        self.logger.debug('Including %s', filename)
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
    """ This class processes a sequence of tokens one by one """
    logger = logging.getLogger('preprocessor')

    def __init__(self, line):
        self.line = line
        self.tokens = iter(line)
        self.token = None
        self.next_token()

    def __str__(self):
        return 'Ctx({})'.format(''.join(map(str, self.line)))

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


class ExpansionContext(LineEater):
    """ Pushed on the stack when a macro is expanded """
    def __init__(self, line, hidden):
        super().__init__(line)
        self.hidden = hidden


class LineParser(LineEater):
    def consume(self, typ=None):
        if not typ:
            if not self.peak:
                self.error('Expecting extra tokens')
            else:
                typ = self.peak

        if self.peak != typ:
            self.error('Expected {} but got {}'.format(typ, self.peak))

        return self.next_token()

    def has_consumed(self, typ):
        if self.peak == typ:
            self.consume(typ)
            return True
        return False


class Expander:
    """ Per source or header file an expander class is created

    Contains:
    - An if-stack to keep track of if-else nesting levels
    - Contains another stack of macro expansions in progress.
      If a macro is encountered, its contents are pushed on this stack
      and processing continues over there.
    """
    logger = logging.getLogger('preprocessor')

    def __init__(self, context):
        super().__init__()
        self.context = context
        # If-def stack:
        self.if_stack = []
        self.enabled = True

        # A black list of defines currently being expanded:
        self.blue_list = set()

        # A stack of expansion contexts:
        self.expand_stack = []
        self._undo_token = None

        # Other state variables:
        self.in_directive = False

    @property
    def token(self):
        # Look for undo:
        if self._undo_token:
            return self._undo_token

        # look for a token in the stack:
        for ctx in reversed(self.expand_stack):
            if not ctx.at_end:
                return ctx.token

        # As a fallback take the current token:
        if self.in_directive:
            # In a directive, return None at end of line
            if self._token and self._token.first:
                return
            else:
                return self._token
        else:
            return self._token

    def raw_next_token(self):
        t = None
        # First try the undo token:
        if self._undo_token:
            t = self._undo_token
            self._undo_token = None

        # Try a token from the expanding stack:
        while (not t) and self.expand_stack:
            if self.expand_stack[-1].at_end:
                self.pop_context()
            else:
                t = self.expand_stack[-1].next_token()
                # print('Inner token', t)
                break

        # If no more expanding stack, take one of the input:
        if not t:
            t = self._token
            self._token = next(self.tokens, None)
            # print('tokenz', (t.typ, t.first) if t else None)
        return t

    def next_token(self, expand: bool):
        """ Get macro optionally expanded next token """
        t = self.raw_next_token()
        # self.logger.debug('Raw token %s', t)
        if expand:
            while self.expand(t):
                # print('expanded', t)
                t = self.raw_next_token()
                # print('new token', t)
        return t

    @property
    def at_end(self):
        return self.token is None

    @property
    def at_line_start(self):
        return (self.token is None) or self.token.first

    def push_context(self, ctx):
        """ Push a macro expansion """
        self.logger.debug('Pushing context %s', ctx)
        self.expand_stack.append(ctx)
        self.blue_list.add(ctx.hidden)

    def pop_context(self):
        self.logger.debug('Popping context')
        ctx = self.expand_stack.pop(-1)
        self.blue_list.remove(ctx.hidden)

    def consume(self, typ=None, expand=True):
        """ Consume a token of a certain type """
        token = self.next_token(expand)
        if not token:
            self.error('Expecting extra tokens')

        if typ:
            if isinstance(typ, tuple):
                if token.typ not in typ:
                    expected = ','.join(typ)
                    self.error(
                        'Expected {} but got {}'.format(expected, token.typ),
                        token)
            else:
                if token.typ != typ:
                    self.error(
                        'Expected {} but got {}'.format(typ, token.typ), token)
        return token

    def undo(self, token):
        """ Undo token consumption? """
        assert not self._undo_token
        self._undo_token = token

    def has_consumed(self, typ, expand=True):
        token = self.consume(expand=expand)
        if token.typ == typ:
            return True
        else:
            self.undo(token)
            return False

    def eat_line(self):
        """ Eat up all tokens until the end of the line.

        This does not expand macros. """
        line = []
        while not self.at_line_start:
            line.append(self.consume(expand=False))
        return line

    def error(self, msg, token=None):
        if not token:
            token = self.token
        if token:
            raise CompilerError(msg, token.loc)
        else:
            raise CompilerError(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def process(self, tokens):
        """ Process a sequence of tokens into an expanded token sequence.

        This function returns an tokens that must be looped over.
        """
        # Prepare lexer:
        self.tokens = tokens
        self._token = None
        self.raw_next_token()

        # Process the tokens:
        while not self.at_end:
            if self.at_line_start and self.has_consumed('#'):
                # We are inside a directive!
                self.in_directive = True
                for line in self.handle_directive():
                    yield line

                self.in_directive = False

                # Ensure end of line!
                if not self.at_line_start:
                    self.error('Expected end of line')
            else:
                # This is not a directive, but normal text:
                token = self.consume()
                # print('now', token)
                if self.enabled:
                    yield token

        if self.expand_stack:
            # TODO: is this an error?
            pass

        if self.if_stack:
            self.error('#if not properly closed')

    def expand(self, macro_token):
        """ Expand a single token into possibly more tokens! """
        name = macro_token.val
        if self.context.is_defined(name) and name not in self.blue_list:
            macro = self.context.get_define(name)
            if macro.args is None:
                # Macro without arguments
                expansion = macro.value
            else:
                # This macro requires arguments
                token = self.consume()
                if token.typ != '(':
                    self.logger.debug('Not expanding function macro %s', name)
                    self.undo(token)
                    return False
                args = self.gatherargs()
                if len(args) != len(macro.args):
                    self.error(
                        'Got {} arguments ({}), but expected {}'.format(
                            len(args), args, len(macro.args)))

                expansion = self.substitute_arguments(macro, args)

            # Concatenate!
            expansion = self.concatenate(LineParser(expansion))

            # Adjust token spacings of first token to adhere spacing of
            # the macro token:
            if expansion:
                expansion[0] = expansion[0].copy(
                    first=macro_token.first, space=macro_token.space)

            self.logger.debug('Expanding %s', name)
            ctx = ExpansionContext(expansion, name)

            # Expand macro line:
            self.push_context(ctx)
            return True

    def gatherargs(self):
        """ Collect expanded arguments for macro """
        args = []
        parens = 0
        arg = []

        while parens >= 0:
            token = self.consume()
            if token.typ == '(':
                parens += 1

            if token.typ == ')':
                parens -= 1

            if (token.typ == ',' and parens == 0) or (parens < 0):
                # We have a complete argument, add it to the list:
                if arg:
                    # TODO: implement a better check?
                    args.append(arg)
                arg = []
            else:
                arg.append(token)

        return args

    def substitute_arguments(self, macro, args):
        """ Return macro contents with substituted arguments.

        Pay special care to # and ## operators """
        new_line = []
        repl_map = {fp: a for fp, a in zip(macro.args, args)}
        self.logger.debug('replacement map: %s', repl_map)
        sle = LineParser(macro.value)
        while not sle.at_end:
            token = sle.consume()
            if token.typ == '#':
                # Stringify operator '#'!
                arg_name = sle.consume('ID')
                if arg_name.val in repl_map:
                    new_line.append(self.stringify(
                        token, repl_map[arg_name.val], arg_name.loc))
                else:
                    sle.error(
                        '{} does not refer a macro argument'.format(
                            arg_name.val))
            elif token.typ == 'ID' and token.val in repl_map:
                replacement = repl_map[token.val]
                first = True
                for rt in replacement:
                    if first:
                        rt2 = rt.copy(space=token.space)
                    else:
                        rt2 = rt.copy()
                    new_line.append(rt2)
                    first = False
            else:
                new_line.append(token)

        return new_line

    def stringify(self, hash_token, snippet, loc):
        """ Handle the '#' stringify operator """
        string_value = '"{}"'.format(''.join(map(str, snippet)))
        return CToken('STRING', string_value, hash_token.space, False, loc)

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
                        self.error('Cannot glue {}'.format(le.peak))
                    lhs = CToken(
                        'ID', lhs.val + rhs, lhs.space, lhs.first, lhs.loc)
                glue_line.append(lhs)
            else:
                glue_line.append(le.consume())
        return glue_line

    def make_newline_token(self, line):
        raise NotImplementedError()
        # return CToken('BOL', '', '', True, Location(line))

    def handle_directive(self):
        """ Handle a single preprocessing directive """
        token = self.consume('ID')
        new_line_token = CToken('WS', '', '', True, token.loc)
        directive = token.val
        if directive == 'ifdef':
            if self.enabled:
                test_define = self.consume('ID', expand=False).val
                condition = self.context.is_defined(test_define)
                self.if_stack.append(IfState(condition))
            else:
                self.eat_line()
                self.if_stack.append(IfState(True))

            self.calculate_active()
        elif directive == 'if':
            if self.enabled:
                condition = bool(self.eval_expr())
                self.if_stack.append(IfState(condition))
            else:
                self.eat_line()
                self.if_stack.append(IfState(True))
            self.calculate_active()
        elif directive == 'elif':
            if not self.if_stack:
                self.error('#elif outside #if', token)

            if self.if_stack[-1].in_else:
                self.error('#elif after #else', token)

            if self.enabled:
                condition = bool(self.eval_expr())
                self.if_stack[-1].condition = condition
            else:
                self.eat_line()

            self.calculate_active()
        elif directive == 'else':
            if not self.if_stack:
                self.error('#else outside #if', token)

            if self.if_stack[-1].in_else:
                self.error('One else too much in #ifdef', token)

            self.if_stack[-1].in_else = True
            self.calculate_active()
        elif directive == 'ifndef':
            if self.enabled:
                test_define = self.consume('ID', expand=False).val
                condition = not self.context.is_defined(test_define)
                self.if_stack.append(IfState(condition))
            else:
                self.eat_line()
                self.if_stack.append(IfState(True))

            self.calculate_active()
        elif directive == 'endif':
            if not self.if_stack:
                self.error('Mismatching #endif', token)
            self.if_stack.pop(-1)
            self.calculate_active()
        elif directive == 'include':
            if self.enabled:
                token = self.consume()
                if token.typ == '<':
                    # TODO: this is a bad way of getting the filename:
                    filename = ''
                    token = self.consume()
                    while token.typ != '>':
                        filename += str(token)
                        token = self.consume()
                    include_filename = filename
                else:
                    include_filename = token.val[1:-1]

                for line in self.context.include(include_filename):
                    yield line
            else:
                self.eat_line()
        elif directive == 'define':
            if self.enabled:
                name = self.consume('ID', expand=False)

                # Handle function like macros:
                token = self.consume(expand=False)
                if token.typ == '(' and not token.space:
                    args = []
                    if not self.has_consumed(')', expand=False):
                        args.append(self.consume('ID', expand=False).val)
                        while self.has_consumed(',', expand=False):
                            args.append(self.consume('ID', expand=False).val)
                        self.consume(')', expand=False)
                else:
                    self.undo(token)
                    args = None

                # Grab the value of the macro:
                value = self.eat_line()
                if value:
                    # Patch first token spaces:
                    value[0] = value[0].copy(space='')
                value_txt = ''.join(map(str, value))
                macro = Macro(name.val, args, value)
                self.logger.debug('Defining %s=%s', name.val, value_txt)
                self.context.define(macro)
            else:
                self.eat_line()
        elif directive == 'undef':
            if self.enabled:
                name = self.consume('ID', expand=False).val
                self.context.undefine(name)
            else:
                self.eat_line()
        elif directive == 'line':
            line = self.consume('NUMBER').val
            filename = self.consume('STRING').val
            flags = []
            token = self.consume()
            while token.typ == 'NUMBER':
                flags.append(token.val)
                token = self.consume()
            self.undo(token)
        elif directive == 'error':
            message = ''.join(map(str, self.eat_line()))
            if self.enabled:
                self.error(message, token)
        elif directive == 'warning':
            message = ''.join(map(str, self.eat_line()))
            if self.enabled:
                self.warning(message)
        else:
            self.logger.error('todo: %s', directive)
            raise NotImplementedError(directive)
        # Return an empty newline token!
        yield new_line_token

    def calculate_active(self):
        """ Determine if we may emit code given the current if-stack """
        if self.if_stack:
            self.enabled = all(i.may_encode for i in self.if_stack)
        else:
            self.enabled = True

    def eval_expr(self):
        """ Evaluate an expression """
        return self.parse_expression()

    def parse_expression(self, priority=0):
        """ Parse an expression in an #if

        Idea taken from: https://github.com/shevek/jcpp/blob/master/
            src/main/java/org/anarres/cpp/Preprocessor.java
        """
        token = self.consume()
        if token.typ == '!':
            lhs = int(not(bool(self.parse_expression(11))))
        elif token.typ == '-':
            lhs = -self.parse_expression(11)
        elif token.typ == '+':
            lhs = -self.parse_expression(11)
        elif token.typ == '~':
            lhs = ~self.parse_expression(11)
        elif token.typ == '(':
            lhs = self.parse_expression(0)
            self.consume(')')
        elif token.typ == 'ID':
            name = token.val
            if name == 'defined':
                # self.logger.debug('Checking for "defined"')
                if self.has_consumed('(', expand=False):
                    test_define = self.consume('ID', expand=False).val
                    self.consume(')', expand=False)
                else:
                    test_define = self.consume('ID', expand=False).val
                lhs = int(self.context.is_defined(test_define))
                self.logger.debug('Defined %s = %s', test_define, lhs)
            else:
                self.logger.warning('Attention: undefined "%s"', name)
                lhs = 0
        elif token.typ == 'NUMBER':
            lhs = cnum(token.val)
        else:
            raise NotImplementedError(token.val)

        op_map = {
            '*': (11, operator.mul),
            '/': (11, operator.floordiv),
            '%': (11, operator.mod),
            '+': (10, operator.add),
            '-': (10, operator.sub),
            '<<': (9, operator.lshift),
            '>>': (9, operator.rshift),
            '<': (8, lambda x, y: int(x < y)),
            '>': (8, lambda x, y: int(x > y)),
            '<=': (8, lambda x, y: int(x <= y)),
            '>=': (8, lambda x, y: int(x >= y)),
            '==': (7, lambda x, y: int(x == y)),
            '!=': (7, lambda x, y: int(x != y)),
            '&': (6, operator.and_),
            '^': (5, operator.xor),
            '|': (4, operator.or_),
            '&&': (3, lambda x, y: int(bool(x) and bool(y))),
            '||': (2, lambda x, y: int(bool(x) or bool(y))),
            '?': (1, None),
        }

        while True:
            # This would be the next operator:
            token = self.consume()
            op = token.typ

            # Determine if the operator has a low enough priority:
            pri = op_map[op][0] if op in op_map else None
            if (pri is None) or (pri <= priority):
                self.undo(token)
                break

            # We are go, eat the right hand side
            rhs = self.parse_expression(pri)

            if op in op_map:
                func = op_map[op][1]
                if func:
                    lhs = func(lhs, rhs)
                elif op == '?':
                    self.consume(':')
                    false_result = self.parse_expression(0)
                    lhs = rhs if lhs != 0 else false_result
                else:
                    raise NotImplementedError(op)
            else:
                raise NotImplementedError(op)

        return lhs


def cnum(txt):
    """ Convert C number to integer """
    if isinstance(txt, int):
        return txt
    if txt.endswith(('L', 'U')):
        return int(txt[:-1])
    else:
        return int(txt)


class Macro:
    """ Macro define """
    def __init__(self, name, args, value, protected=False):
        self.name = name
        self.args = args
        self.value = value
        self.protected = False


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
    def dump(self, tokens, file=None):
        first_line = True
        for token in tokens:
            # print(token.typ, token.val, token.first)
            if token.first:
                # Insert newline!
                if first_line:
                    first_line = False
                else:
                    print(file=file)
            text = str(token)
            print(text, end='', file=file)


def lines_to_tokens(lines):
    """ Generate a stream of tokens from lines of tokens """
    for line in lines:
        for token in line:
            yield token


def skip_ws(tokens):
    """ Filter whitespace tokens """
    for token in tokens:
        if token.typ in ['WS', 'BOL']:
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

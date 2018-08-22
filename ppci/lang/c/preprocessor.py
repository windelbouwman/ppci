""" C preprocessor.

This file contains an implementation of the C preprocessor.

Each token has info about the amount
of whitespace preceeding the token and whether it is the first token on
a line.

Sourcecode of inspiration:

- https://github.com/shevek/jcpp/blob/master/src/main/java/org/anarres/cpp/
  Preprocessor.java
- https://github.com/drh/lcc/blob/master/cpp/macro.c
"""

import os
import logging
import operator
import time

from ...common import CompilerError, SourceLocation
from .lexer import CLexer, CToken, lex_text
from .utils import cnum, charval, replace_escape_codes


class CPreProcessor:
    """ A pre-processor for C source code """
    logger = logging.getLogger('preprocessor')

    def __init__(self, coptions):
        self.coptions = coptions
        self.verbose = coptions['verbose']
        self.defines = {}
        self.filename = None

        # A black list of defines currently being expanded:
        self.blue_list = set()
        self.predefine_builtin_macros()

    def predefine_builtin_macros(self):
        """ Define predefined macros """
        internal_loc = SourceLocation(None, 1, 1, 1)

        # Indicate standard C:
        self.define(
            Macro(
                '__STDC__',
                [CToken('NUMBER', '1', '', False, internal_loc)],
                protected=True))

        # Indicate C99 version:
        if self.coptions['std'] == 'c99':
            self.define(
                Macro(
                    '__STDC_VERSION__',
                    [CToken('NUMBER', '199901L', '', False, internal_loc)],
                    protected=True))

        # Set c11 version:
        if self.coptions['std'] == 'c11':
            self.define(
                Macro(
                    '__STDC_VERSION__',
                    [CToken('NUMBER', '201112L', '', False, internal_loc)],
                    protected=True))

        # Special macros:
        self.define(FunctionMacro('__LINE__', self.special_macro_line))
        self.define(FunctionMacro('__FILE__', self.special_macro_file))
        self.define(FunctionMacro('__DATE__', self.special_macro_date))
        self.define(FunctionMacro('__TIME__', self.special_macro_time))

        # Misc macros:
        self.define(
            Macro(
                '__BYTE_ORDER__',
                [CToken('NUMBER', '1L', '', False, internal_loc)],
                protected=True))
        self.define(
            Macro(
                '__ORDER_LITTLE_ENDIAN__',
                [CToken('NUMBER', '1L', '', False, internal_loc)],
                protected=True))

        # Macro's defines by options:
        for macro in self.coptions.macros:
            logging.debug('Setting predefined macro %s', macro)
            self.define(
                Macro(
                    macro,
                    [CToken('NUMBER', '1', '', False, internal_loc)]))

    def special_macro_line(self, macro_token):
        """ Invoked when the __LINE__ macro is expanded """
        return [CToken(
            'NUMBER', str(macro_token.loc.row),
            macro_token.space, macro_token.first,
            macro_token.loc)]

    def special_macro_file(self, macro_token):
        """ Invoked when the __FILE__ macro is expanded """
        value = str(macro_token.loc.filename)
        return [CToken(
            'STRING', '"{}"'.format(value),
            macro_token.space, macro_token.first,
            macro_token.loc)]

    def special_macro_date(self, macro_token):
        """ Invoked when the __DATE__ macro is expanded """
        value = time.strftime('%b %d %Y')
        return [CToken(
            'STRING', '"{}"'.format(value),
            macro_token.space, macro_token.first,
            macro_token.loc)]

    def special_macro_time(self, macro_token):
        value = time.strftime('%H:%M:%S')
        return [CToken(
            'STRING', '"{}"'.format(value),
            macro_token.space, macro_token.first,
            macro_token.loc)]

    def process(self, f, filename=None):
        """ Process the given open file into expanded lines of tokens """
        self.logger.debug('Processing %s', filename)
        previous_filename = self.filename
        self.filename = filename
        clexer = CLexer(self.coptions)
        tokens = clexer.lex(f, filename)
        macro_expander = Expander(self)
        yield LineInfo(1, filename)
        for token in macro_expander.process(tokens):
            yield token
        self.logger.debug('Finished %s', filename)
        self.filename = previous_filename

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

    def include(self, filename, loc, use_current_dir=False):
        """ Turn the given filename into a series of lines """
        self.logger.debug('Including %s', filename)
        search_directories = []
        if use_current_dir:
            # In the case of: #include "foo.h"
            current_dir = os.path.dirname(self.filename)
            search_directories.append(current_dir)
        search_directories.extend(self.coptions.include_directories)
        # self.logger.debug((search_directories)
        for path in search_directories:
            full_path = os.path.join(path, filename)
            if os.path.exists(full_path):
                self.logger.debug('Including %s', full_path)
                with open(full_path, 'r') as f:
                    for line in self.process(f, full_path):
                        yield line
                return
        self.logger.error('File not found: %s', filename)
        raise CompilerError('Could not find {}'.format(filename), loc)


class LineEater:
    """ This class processes a sequence of tokens one by one """
    logger = logging.getLogger('preprocessor')

    def __init__(self, line):
        self.line = line
        self.tokens = iter(line)
        self.token = None
        self._prev_token = None
        self._current_token = None
        self.next_token()

    def __str__(self):
        return 'Ctx({})'.format(''.join(map(str, self.line)))

    @property
    def peak(self):
        if self.token:
            return self.token.typ

    @property
    def previous(self):
        if self._prev_token:
            return self._prev_token.typ

    @property
    def at_end(self):
        return self.token is None

    def next_token(self):
        self._prev_token = self._current_token
        self._current_token = self.token
        self.token = next(self.tokens, None)
        return self._current_token


class TokenExpansion(LineEater):
    """ Pushed on the stack when a macro is expanded """
    def __init__(self, line, hidden=()):
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

    def __init__(self, preprocessor):
        super().__init__()
        self.preprocessor = preprocessor
        self.verbose = preprocessor.verbose
        # If-def stack:
        self.if_stack = []
        self.enabled = True

        # A stack of expansion contexts:
        self.expand_stack = []
        self.paren_level = 0
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
        if t and expand:
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
        if self.verbose:
            self.logger.debug('Pushing context %s', ctx)
        self.expand_stack.append(ctx)
        for item in ctx.hidden:
            self.preprocessor.blue_list.add(item)

    def pop_context(self):
        if self.verbose:
            self.logger.debug('Popping context')
        ctx = self.expand_stack.pop(-1)
        for item in ctx.hidden:
            self.preprocessor.blue_list.remove(item)

    def consume(self, typ=None, expand=True, stop_eol=False):
        """ Consume a token of a certain type """
        token = self.next_token(expand)
        # TODO: where to check for end of file?
        # if not token:
        #     self.error('Expecting extra tokens')

        # Stop on new line:
        if token and stop_eol and token.first:
            self.undo(token)
            token = None

        # Check certain type
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
        token = self.next_token(True)
        while token:
            if token.first and token.typ == '#':
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
                # print('now', token)
                if self.enabled:
                    yield token
            token = self.next_token(True)

        if self.expand_stack:
            print(self.expand_stack)
            self.error('Not all expansions finished!')

        if self.if_stack:
            self.error('#if not properly closed')

    def expand(self, macro_token):
        """ Expand a single token into possibly more tokens.

        This works by expanding the macro and placing the replacement
        on the 'context stack'
        """
        name = macro_token.val
        if self.preprocessor.is_defined(name) and \
                name not in self.preprocessor.blue_list:
            macro = self.preprocessor.get_define(name)
            if isinstance(macro, FunctionMacro):
                # Special macro:
                expansion = macro.function(macro_token)
            elif macro.args is None:
                # Macro without arguments
                expansion = macro.value
            else:
                # This macro requires arguments
                token = self.consume()
                if not token or token.typ != '(':
                    self.logger.debug('Not expanding function macro %s', name)
                    self.undo(token)
                    return False
                args = self.gatherargs()
                if macro.variadic:
                    if len(args) < len(macro.args):
                        self.error(
                            'Got {} arguments ({})'
                            ', but required at least {}'.format(
                                len(args), args, len(macro.args)))
                else:
                    if len(args) != len(macro.args):
                        self.error(
                            'Got {} arguments ({}), but expected {}'.format(
                                len(args), args, len(macro.args)))

                expansion = self.substitute_arguments(macro, args)

            # Concatenate!
            expansion = self.concatenate(expansion)

            # Adjust token spacings of first token to adhere spacing of
            # the macro token:
            if expansion:
                expansion[0] = expansion[0].copy(
                    first=macro_token.first, space=macro_token.space)

            if self.verbose:
                self.logger.debug('Expanding %s', name)
            ctx = TokenExpansion(expansion, [name])

            # Expand macro line:
            self.push_context(ctx)
            return True

    def gatherargs(self):
        """ Collect expanded arguments for macro """
        args = []
        parens = 0
        arg = []

        while parens >= 0:
            token = self.consume(expand=False)
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

    def expand_token_sequence(self, tokens):
        """ Expand a sequence of tokens """
        expander = Expander(self.preprocessor)
        a = list(expander.process(iter(tokens)))
        # print(a)
        return a

    def substitute_arguments(self, macro, args):
        """ Return macro contents with substituted arguments.

        Pay special care to # and ## operators """
        new_line = []
        # print(args)
        # expanded_args = [self.expand_token_sequence(a) for a in args]
        # Create two variants: expanded and not expanded:
        repl_map = {
            fp: (self.expand_token_sequence(a), a)
            for fp, a in zip(macro.args, args)}
        # print(repl_map)
        if self.verbose:
            self.logger.debug('replacement map: %s', repl_map)
        sle = LineParser(macro.value)
        while not sle.at_end:
            token = sle.consume()
            if token.typ == '#':
                # Stringify operator '#'!
                # Use the unexpanded version for this one
                arg_name = sle.consume('ID')
                if arg_name.val in repl_map:
                    new_line.append(self.stringify(
                        token, repl_map[arg_name.val][1], arg_name.loc))
                else:
                    sle.error(
                        '{} does not refer a macro argument'.format(
                            arg_name.val))
            elif token.typ == 'ID' and token.val in repl_map:
                # TODO: maybe figure out a better way for this peaking at '##'
                if sle.previous == '##' or sle.peak == '##':
                    # Used in '##' construction!
                    replacement = repl_map[token.val][1]
                else:
                    # Pick the expanded variant here:
                    replacement = repl_map[token.val][0]
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

    def concat(self, lhs, rhs):
        """ Concatenate two tokens """
        total_text = lhs.val + rhs.val

        # Invoke the lexer again on glued text to produce tokens:
        tokens = lex_text(total_text, self.preprocessor.coptions)
        if len(tokens) == 1:
            return tokens[0].copy(space=lhs.space, first=lhs.first)
        else:
            self.error('Invalidly glued "{}"'.format(total_text), token=lhs)

    def concatenate(self, tokens):
        """ Handle the '##' token concatenation operator """
        le = LineParser(tokens)
        glue_line = []
        while not le.at_end:
            lhs = le.consume()
            while le.has_consumed('##'):
                rhs = le.consume()
                lhs = self.concat(lhs, rhs)
            glue_line.append(lhs)
        return glue_line

    def make_newline_token(self, line):
        raise NotImplementedError()
        # return CToken('BOL', '', '', True, Location(line))

    def handle_directive(self):
        """ Handle a single preprocessing directive """
        directive_token = self.consume('ID')
        new_line_token = CToken('WS', '', '', True, directive_token.loc)
        directive = directive_token.val
        if directive == 'ifdef':
            if self.enabled:
                test_define = self.consume(
                    'ID', expand=False, stop_eol=True).val
                condition = self.preprocessor.is_defined(test_define)
                self.if_stack.append(IfState(condition))
            else:
                self.eat_line()
                self.if_stack.append(IfState(True))

            self.calculate_active()
            yield new_line_token
        elif directive == 'ifndef':
            if self.enabled:
                test_define = self.consume(
                    'ID', expand=False, stop_eol=True).val
                condition = not self.preprocessor.is_defined(test_define)
                self.if_stack.append(IfState(condition))
            else:
                self.eat_line()
                self.if_stack.append(IfState(True))

            self.calculate_active()
            yield new_line_token
        elif directive == 'if':
            if self.enabled:
                condition = bool(self.eval_expr())
                self.if_stack.append(IfState(condition))
            else:
                self.eat_line()
                self.if_stack.append(IfState(True))
            self.calculate_active()
            yield new_line_token
        elif directive == 'elif':
            if not self.if_stack:
                self.error('#elif outside #if', directive_token)

            if self.if_stack[-1].in_else:
                self.error('#elif after #else', directive_token)

            if self.calc_enabled(self.if_stack[:-1]):
                can_else = not self.if_stack[-1].was_active
                condition = bool(self.eval_expr()) and can_else
                self.if_stack[-1].active = condition
                if condition:
                    self.if_stack[-1].was_active = True
            else:
                self.eat_line()

            self.calculate_active()
            yield new_line_token
        elif directive == 'else':
            if not self.if_stack:
                self.error('#else outside #if', directive_token)

            if self.if_stack[-1].in_else:
                self.error('One else too much in #ifdef', directive_token)

            self.if_stack[-1].in_else = True
            self.if_stack[-1].active = not self.if_stack[-1].was_active
            self.calculate_active()
            yield new_line_token
        elif directive == 'endif':
            if not self.if_stack:
                self.error('Mismatching #endif', directive_token)
            self.if_stack.pop(-1)
            self.calculate_active()
            yield new_line_token
        elif directive == 'include':
            if self.enabled:
                token = self.consume(('<', 'STRING'))
                if token.typ == '<':
                    use_current_dir = False
                    # TODO: this is a bad way of getting the filename:
                    filename = ''
                    token = self.consume()
                    while token.typ != '>':
                        filename += str(token)
                        token = self.consume()
                    include_filename = filename
                else:
                    use_current_dir = True
                    include_filename = token.val[1:-1]

                for token in self.preprocessor.include(
                        include_filename, directive_token.loc,
                        use_current_dir=use_current_dir):
                    yield token

                yield LineInfo(
                    directive_token.loc.row + 1,
                    directive_token.loc.filename,
                    flags=[LineInfo.FLAG_RETURN_FROM_INCLUDE])
            else:
                self.eat_line()
        elif directive == 'define':
            if self.enabled:
                name = self.consume('ID', expand=False, stop_eol=True)

                # Handle function like macros:
                variadic = False
                token = self.consume(expand=False)
                if token.typ == '(' and not token.space:
                    args = []
                    # if not self.has_consumed(')', expand=False):
                    while True:
                        if self.token.typ == '...':
                            self.consume('...')
                            variadic = True
                            break
                        elif self.token.typ == 'ID':
                            args.append(self.consume('ID', expand=False).val)
                        else:
                            break

                        # Eat comma, and get other arguments
                        if self.has_consumed(','):
                            continue
                        else:
                            break
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
                macro = Macro(name.val, value, args=args, variadic=variadic)
                if self.verbose:
                    self.logger.debug('Defining %s=%s', name.val, value_txt)
                self.preprocessor.define(macro)
            else:
                self.eat_line()
            yield new_line_token
        elif directive == 'undef':
            if self.enabled:
                name = self.consume('ID', expand=False, stop_eol=True).val
                self.preprocessor.undefine(name)
            else:
                self.eat_line()
            yield new_line_token
        elif directive == 'line':
            line = self.consume(typ='NUMBER', stop_eol=True).val
            filename_token = self.consume(stop_eol=True)
            if filename_token:
                if filename_token.typ == 'STRING':
                    filename = filename_token.val
                else:
                    self.error('Expected filename here', token=filename_token)
            # TODO: use line and filename information to adjust lexer?
            # flags = []
            # flag_token = self.consume(stop_eol=True)
            # while flag_token and flag_token.typ == 'NUMBER':
            #    flags.append(token.val)
            #    flag_token = self.consume(stop_eol=True)
            # self.undo(flag_token)
            print(line)
            self.logger.error("#LINE directive not implemented")
            yield new_line_token
        elif directive == 'error':
            message = self.tokens_to_string(self.eat_line())
            if self.enabled:
                self.error(message, directive_token)
            yield new_line_token
        elif directive == 'warning':
            message = self.tokens_to_string(self.eat_line())
            if self.enabled:
                self.warning(message)
            yield new_line_token
        elif directive == 'pragma':
            # Pragma's must be handled, or ignored.
            message = self.tokens_to_string(self.eat_line())
            if self.enabled:
                self.logger.warning('Ignoring pragma: %s', message)
            yield new_line_token
        else:  # pragma: no cover
            self.logger.error('todo: %s', directive)
            self.error('not implemented', directive_token)
            raise NotImplementedError(directive)
        # Return an empty newline token!
        # yield new_line_token

    def tokens_to_string(self, tokens):
        """ Create a text from the given tokens """
        return ''.join(map(str, tokens)).strip()

    def calc_enabled(self, stack):
        if stack:
            return all(i.active for i in stack)
        else:
            return True

    def calculate_active(self):
        """ Determine if we may emit code given the current if-stack """
        if self.if_stack:
            self.enabled = all(i.active for i in self.if_stack)
        else:
            self.enabled = True

    def eval_expr(self):
        """ Evaluate an expression """
        ast_tree = self.parse_expression()
        return self._eval_tree(ast_tree)

    OP_MAP = {
        '*': (11, False, operator.mul),
        '/': (11, False, operator.floordiv),
        '%': (11, False, operator.mod),
        '+': (10, False, operator.add),
        '-': (10, False, operator.sub),
        '<<': (9, False, operator.lshift),
        '>>': (9, False, operator.rshift),
        '<': (8, False, lambda x, y: int(x < y)),
        '>': (8, False, lambda x, y: int(x > y)),
        '<=': (8, False, lambda x, y: int(x <= y)),
        '>=': (8, False, lambda x, y: int(x >= y)),
        '==': (7, False, lambda x, y: int(x == y)),
        '!=': (7, False, lambda x, y: int(x != y)),
        '&': (6, False, operator.and_),
        '^': (5, False, operator.xor),
        '|': (4, False, operator.or_),
        '&&': (3, False, lambda x, y: int(bool(x) and bool(y))),
        '||': (2, False, lambda x, y: int(bool(x) or bool(y))),
        '?': (1, True, None),
    }

    def parse_expression(self, priority=0):
        """ Parse an expression in an #if

        Idea taken from: https://github.com/shevek/jcpp/blob/master/
            src/main/java/org/anarres/cpp/Preprocessor.java
        """
        token = self.consume()
        if token.first and self.paren_level == 0:
            self.undo(token)
            return

        if token.typ == '!':
            lhs = Unop('!', self.parse_expression(11))
        elif token.typ == '-':
            lhs = Unop('-', self.parse_expression(11))
        elif token.typ == '+':
            lhs = self.parse_expression(11)
        elif token.typ == '~':
            lhs = Unop('~', self.parse_expression(11))
        elif token.typ == '(':
            self.paren_level += 1
            lhs = self.parse_expression()
            self.consume(')')
            self.paren_level -= 1
        elif token.typ == 'ID':
            name = token.val
            if name == 'defined':
                # self.logger.debug('Checking for "defined"')
                if self.has_consumed('(', expand=False):
                    test_define = self.consume('ID', expand=False).val
                    self.consume(')', expand=False)
                else:
                    test_define = self.consume('ID', expand=False).val
                lhs = int(self.preprocessor.is_defined(test_define))
                if self.verbose:
                    self.logger.debug('Defined %s = %s', test_define, lhs)
            else:
                if self.verbose:
                    self.logger.warning('Attention: undefined "%s"', name)
                lhs = 0
            lhs = Const(lhs)
        elif token.typ == 'NUMBER':
            lhs, _ = cnum(token.val)
            # TODO: check type specifier?
            lhs = Const(lhs)
        elif token.typ == 'CHAR':
            lhs, _ = charval(replace_escape_codes(token.val))
            # TODO: check type specifier?
            lhs = Const(lhs)
        else:
            raise NotImplementedError(token.val)

        while True:
            # This would be the next operator:
            token = self.consume()

            # Stop at end of line:
            if token.first and self.paren_level == 0:
                self.undo(token)
                break

            op = token.typ

            # Determine if the operator has a low enough priority:
            if op in self.OP_MAP:
                op_prio, right_associative = self.OP_MAP[op][:2]
                left_associative = not right_associative
                if left_associative and (op_prio >= priority):
                    pass
                elif right_associative and (op_prio > priority):
                    pass
                else:
                    self.undo(token)
                    break
            else:
                self.undo(token)
                break

            if op == '?':
                # Eat middle part
                middle = self.parse_expression()
                self.consume(':')
            else:
                middle = None

            # We are go, eat the right hand side
            rhs = self.parse_expression(op_prio)

            if op in self.OP_MAP:
                func = self.OP_MAP[op][2]
                if func:
                    lhs = Binop(lhs, op, rhs)
                elif op == '?':
                    lhs = Ternop(lhs, middle, rhs)
                    # middle if lhs != 0 else rhs
                else:  # pragma: no cover
                    raise NotImplementedError(op)
            else:  # pragma: no cover
                raise NotImplementedError(op)

        return lhs

    def _eval_tree(self, expr):
        """ Evaluate a parsed tree """
        if isinstance(expr, Const):
            return expr.value
        elif isinstance(expr, Unop):
            a = self._eval_tree(expr.a)
            if expr.op == '!':
                return int(not bool(a))
            elif expr.op == '-':
                return -a
            elif expr.op == '~':
                return ~a
            else:  # pragma: no cover
                raise NotImplementedError(expr.op)
        elif isinstance(expr, Binop):
            if expr.op == '||':
                # Short circuit logic:
                a = self._eval_tree(expr.a)
                if a:
                    return True
                else:
                    return self._eval_tree(expr.b)
            elif expr.op == '&&':
                # Short circuit logic:
                a = self._eval_tree(expr.a)
                if a:
                    return self._eval_tree(expr.b)
                else:
                    return False
            else:
                func = self.OP_MAP[expr.op][2]
                return func(self._eval_tree(expr.a), self._eval_tree(expr.b))
        elif isinstance(expr, Ternop):
            a = self._eval_tree(expr.a)
            if a:
                return self._eval_tree(expr.b)
            else:
                return self._eval_tree(expr.c)
        else:  # pragma: no cover
            raise NotImplementedError(str(expr))


class Const:
    def __init__(self, value):
        self.value = value


class Unop:
    def __init__(self, op, a):
        self.op = op
        self.a = a


class Binop:
    def __init__(self, a, op, b):
        self.a = a
        self.op = op
        self.b = b


class Ternop:
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c


class BaseMacro:
    """ Base macro """
    def __init__(self, name, protected=False):
        self.name = name
        self.protected = protected


class Macro(BaseMacro):
    """ Macro define """
    def __init__(self, name, value, args=None, protected=False, variadic=False):
        super().__init__(name, protected=protected)
        self.value = value
        self.args = args
        self.variadic = variadic


class FunctionMacro(BaseMacro):
    """ Special macro, like __FILE__ """
    def __init__(self, name, function):
        super().__init__(name, protected=True)
        self.function = function


class IfState:
    """ If status for use on the if-stack """
    def __init__(self, active):
        self.active = active
        self.was_active = active
        self.in_else = False  # Indicator whether we are in the else clause.


class LineInfo:
    """ Line information indicating where the following content comes from.

    Flags can be given.
    1: start of new file
    2: returning to a file after an include
    3: the following comes from a system header file
    4: The following should be wrapped inside extern "C" implicitly """
    FLAG_START_OF_NEW_FILE = 1
    FLAG_RETURN_FROM_INCLUDE = 2

    def __init__(self, line, filename, flags=()):
        self.line = line
        self.filename = filename
        self.flags = flags

    def __str__(self):
        if self.flags:
            flags = ' ' + ' '.join(map(str, self.flags))
        else:
            flags = ''
        return '# {} "{}"{}'.format(self.line, self.filename, flags)


class CTokenPrinter:
    """ Printer that can turn a stream of token-lines into text """
    def dump(self, tokens, file=None):
        first_line = True
        for token in tokens:
            # print(token.typ, token.val, token.first)
            if isinstance(token, LineInfo):
                # print(token, str(token))
                print(str(token), file=file)
                first_line = True
            else:
                if token.first:
                    # Insert newline!
                    if first_line:
                        first_line = False
                    else:
                        print(file=file)
                text = str(token)
                print(text, end='', file=file)


def skip_ws(tokens):
    """ Filter whitespace tokens """
    for token in tokens:
        if isinstance(token, LineInfo):
            pass
        elif token.typ in ['WS', 'BOL']:
            pass
        else:
            yield token


def string_convert(tokens):
    """ Phase 5 of compilation.

    Process escaped string constants into unicode. """
    # Process
    for token in tokens:
        if token.typ in ['STRING', 'CHAR']:
            token.val = replace_escape_codes(token.val)
        yield token


def string_concat(tokens):
    """ Merge adjacent string literals into single tokens.

    This is phase 6 of compilation. """
    string_token = None
    for token in tokens:
        if token.typ == 'STRING':
            if string_token:
                string_token.val += token.val
            else:
                string_token = token
        else:
            if string_token:
                yield string_token
                string_token = None
            yield token

    if string_token:
        yield string_token


def prepare_for_parsing(tokens, keywords):
    """ Strip out tokens on the way from preprocessor to parser.

    Apply several modifications on the token stream to adapt it
    to the format that the parser requires.

    This involves:
    - Removal of whitespace
    - Changing some id's into keywords
    - Concatenation of adjacent string literals.
    """
    for token in string_concat(string_convert(skip_ws(tokens))):
        if token.typ == 'ID':
            if token.val in keywords:
                token.typ = token.val
            yield token
        else:
            yield token

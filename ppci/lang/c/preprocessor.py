""" C preprocessor.

This file contains an implementation of the C preprocessor.

Each token has info about the amount
of whitespace preceeding the token and whether it is the first token on
a line.

Sourcecode of inspiration:

- https://github.com/shevek/jcpp/blob/master/src/main/java/org/anarres/cpp/
  Preprocessor.java
- https://github.com/drh/lcc/blob/master/cpp/macro.c
- https://github.com/rui314/8cc/blob/master/cpp.c
"""

import os
import logging
import operator
import time

from ...common import CompilerError
from .lexer import CLexer, CToken, lex_text, SourceFile
from .utils import cnum, charval, replace_escape_codes, LineInfo
from .macro import Macro, FunctionMacro
from .nodes import types, expressions


class CPreProcessor:
    """ A pre-processor for C source code """

    logger = logging.getLogger("preprocessor")

    def __init__(self, coptions):
        self.coptions = coptions
        self.verbose = coptions["verbose"]
        self.macros = {}  # A mapping of macros
        self.files = []  # Stack of included files.
        self.counter = 0  # For the __COUNTER__ macro
        self._int_type = types.BasicType(types.BasicType.INT)

        self.predefine_builtin_macros()

    def predefine_builtin_macros(self):
        """ Define predefined macros """

        # Indicate standard C:
        self.define_object_macro("__STDC__", "1", protected=True)

        # Hosted or freestanding:
        hosted = "0" if self.coptions["freestanding"] else "1"
        self.define_object_macro("__STDC_HOSTED__", hosted, protected=True)

        # Set c99/c11 version:
        if self.coptions["std"] == "c99":
            self.define_object_macro(
                "__STDC_VERSION__", "199901L", protected=True
            )
        elif self.coptions["std"] == "c11":
            self.define_object_macro(
                "__STDC_VERSION__", "201112L", protected=True
            )

        # Special macros:
        self.define_special_macro("__LINE__", self.special_macro_line)
        self.define_special_macro("__FILE__", self.special_macro_file)
        self.define_special_macro("__DATE__", self.special_macro_date)
        self.define_special_macro("__TIME__", self.special_macro_time)

        # Extra macros:
        self.define_special_macro("__COUNTER__", self.special_macro_counter)
        self.define_special_macro(
            "__INCLUDE_LEVEL__", self.special_macro_include_level
        )

        # Misc macros:
        self.define_object_macro("__BYTE_ORDER__", "1L", protected=True)
        self.define_object_macro(
            "__ORDER_LITTLE_ENDIAN__", "1L", protected=True
        )

        # Macro's defines by options:
        for name, value in self.coptions.macros:
            self.logger.debug("Defining %s=%s", name, value)
            self.define_object_macro(name, value)

        for name in self.coptions.undefine_macros:
            self.logger.debug("Undefining %s", name)
            self.undefine(name)

    def special_macro_line(self, macro_token):
        """ Invoked when the __LINE__ macro is expanded """
        value = str(macro_token.loc.row)
        return [self.make_token(macro_token, "NUMBER", value)]

    def special_macro_file(self, macro_token):
        """ Invoked when the __FILE__ macro is expanded """
        value = '"{}"'.format(macro_token.loc.filename)
        return [self.make_token(macro_token, "STRING", value)]

    def special_macro_date(self, macro_token):
        """ Invoked when the __DATE__ macro is expanded """
        value = time.strftime('"%b %d %Y"')
        return [self.make_token(macro_token, "STRING", value)]

    def special_macro_time(self, macro_token):
        """ Implement __TIME__ macro """
        value = time.strftime('"%H:%M:%S"')
        return [self.make_token(macro_token, "STRING", value)]

    def special_macro_counter(self, macro_token):
        """ Implement __COUNTER__ macro """
        value = str(self.counter)
        self.counter += 1
        return [self.make_token(macro_token, "NUMBER", value)]

    def special_macro_include_level(self, macro_token):
        """ Implement __INCLUDE_LEVEL__ macro """
        value = str(len(self.files))
        return [self.make_token(macro_token, "NUMBER", value)]

    @staticmethod
    def make_token(from_token, typ, value):
        """ Create a new token from another token. """
        return CToken(
            typ, value, from_token.space, from_token.first, from_token.loc
        )

    # Macro related functions:
    def define_special_macro(self, name, handler):
        """ Define a spcial macro which has a callback function. """
        self.define(FunctionMacro(name, handler))

    def define_object_macro(self, name, text, protected=False):
        """ Define an object like macro. """
        tokens = lex_text(text, self.coptions)
        macro = Macro(name, tokens, protected=protected)
        self.define(macro)

    def define(self, macro):
        """ Register a macro """
        if self.is_defined(macro.name):
            if self.get_define(macro.name).protected:
                raise CompilerError("Cannot redefine {}".format(macro.name))
        self.macros[macro.name] = macro

    def undefine(self, name: str):
        """ Kill a define! """
        if self.is_defined(name):
            self.macros.pop(name)

    def is_defined(self, name: str) -> bool:
        """ Check if the given define is defined. """
        return name in self.macros

    def get_define(self, name: str):
        """ Retrieve the given define! """
        return self.macros[name]

    def in_hideset(self, name):
        """ Test if the given macro is contained in the current hideset. """
        if self.files[-1].macro_expansions:
            return name in self.files[-1].macro_expansions[-1].hideset
        else:
            return False

    def process_file(self, f, filename=None):
        """ Process the given open file into tokens. """
        self.logger.debug("Processing %s", filename)
        source_file = SourceFile(filename)
        clexer = CLexer(self.coptions)
        tokens = clexer.lex(f, source_file)
        ex = FileExpander(source_file, tokens)
        self.files.append(ex)
        yield LineInfo(1, source_file.filename)
        for token in self.process_tokens():
            yield token

        # Test for empty if-stack:
        if self.files[-1].if_stack:
            hints = []
            for if_clause in self.files[-1].if_stack:
                hints.append("This if is not terminated: {}".format(if_clause))
            amount = len(self.files[-1].if_stack)
            self.error(
                "{} #if/ifdef/ifndef directives not closed.".format(amount),
                hints=hints,
                loc=self.files[-1].if_stack[-1].location,
            )

        self.logger.debug("Finished %s", source_file.filename)
        self.files.pop()

    def locate_include(
        self, filename, loc, use_current_dir: bool, include_next
    ):
        """ Determine which file to use given the include filename.

        Parameters:
            - loc: the location where this include is included.
            - use_current_dir: If true, look in the directory of
                the current file.
        """
        self.logger.debug("Locating %s", filename)

        # Maybe it is an absolute path:
        if os.path.isabs(filename):
            if os.path.exists(filename):
                self.logger.debug("Absolute path, not searching include paths")
                return filename
            else:
                self.error(
                    "Absolute filename {} not found".format(filename), loc
                )

        # Determine search paths:
        search_directories = []
        if use_current_dir:
            # In the case of: #include "foo.h"
            current_dir = os.path.dirname(self.files[-1].source_file.filename)
            search_directories.append(current_dir)
        search_directories.extend(self.coptions.include_directories)

        # self.logger.debug((search_directories)
        for path in search_directories:
            self.logger.debug("Searching in %s", path)
            full_path = os.path.join(path, filename)
            if os.path.exists(full_path):
                if include_next:
                    current_filename = self.files[-1].source_file.filename
                    if full_path == current_filename:
                        include_next = False
                else:
                    return full_path

        self.logger.error("File not found: %s", filename)
        raise CompilerError("Could not find {}".format(filename), loc)

    def include(
        self, filename, loc, use_current_dir=False, include_next=False
    ):
        """ Turn the given filename into a series of tokens.
        """
        full_path = self.locate_include(
            filename, loc, use_current_dir, include_next
        )
        self.logger.debug("Including %s", full_path)
        source_file = SourceFile(full_path)
        self.files[-1].dependencies.append(source_file)
        with open(full_path, "r") as f:
            for token in self.process_file(f, full_path):
                yield token

    # Token consume / peeking:
    @property
    def token(self):
        """ Peek one token ahead without taking it. """
        return self.files[-1].peek

    def next_token(self, expand=True):
        """ Get next token """
        token = self.files[-1].next_token()
        if token and expand:
            while self.expand(token):
                token = self.next_token(expand=False)

        if self.verbose:
            self.logger.debug("Token: %s", repr(token))

        return token

    def unget_token(self, token):
        """ Undo token consumption. """
        if self.verbose:
            self.logger.debug("Pushback token: %s", repr(token))

        self.files[-1].unget(token)

    def push_expansion(self, expansion):
        """ Push a macro expansion on the stack. """
        self.files[-1].macro_expansions.append(expansion)

    @property
    def at_end(self):
        return self.token is None

    @property
    def at_line_start(self):
        return (self.token is None) or self.token.first

    def consume(self, typ=None, expand=True):
        """ Consume a token of a certain type """
        token = self.next_token(expand=expand)

        # Check for end of file:
        if not token:
            self.error("Expecting here: {}, but got nothing".format(typ))

        # Check certain type
        if typ:
            if isinstance(typ, tuple):
                if token.typ not in typ:
                    expected = ", ".join(typ)
                    self.error(
                        "Expected {} but got {}".format(expected, token.typ),
                        loc=token.loc,
                    )
            else:
                if token.typ != typ:
                    self.error(
                        "Expected {} but got {}".format(typ, token.typ),
                        loc=token.loc,
                    )
        return token

    def has_consumed(self, typ, expand=True):
        token = self.consume(expand=expand)
        if token.typ == typ:
            return True
        else:
            self.unget_token(token)
            return False

    def eat_line(self):
        """ Eat up all tokens until the end of the line.

        This does not expand macros. """
        line = []
        while not self.at_line_start:
            line.append(self.consume(expand=False))
        return line

    # Output generation:
    def error(self, msg, hints=None, loc=None):
        """ We hit an error condition. """
        # self.logger.error(msg)
        raise CompilerError(msg, hints=hints, loc=loc)

    def warning(self, msg):
        self.logger.warning(msg)

    def process_tokens(self):
        """ Process a sequence of tokens into an expanded token sequence.

        This function returns an tokens that must be looped over.
        """
        assert not self.files[-1].macro_expansions

        # Process the tokens:
        token = self.next_token()
        while token:
            if token.first and token.typ == "#":
                # We are inside a directive!
                for token in self.handle_directive(token.loc):
                    yield token

                # Ensure end of line!
                if not self.at_line_start:
                    self.error("Expected end of line", loc=self.token.loc)
            else:
                # This is not a directive, but normal text:
                yield token
            token = self.next_token()

    def read_expand(self, token):
        while self.expand(token):
            token = self.next_token()
        return token

    # Macro expansion functions:
    def expand(self, macro_token):
        """ Expand a single token into possibly more tokens.

        """
        name = macro_token.val
        in_hideset = self.in_hideset(name)
        # in_hideset = name in macro_token.hideset
        if self.is_defined(name) and not in_hideset:
            if self.verbose:
                self.logger.debug("Expanding macro %s", name)

            macro = self.get_define(name)
            expansion = self.expand_macro(macro, macro_token)
            if expansion is None:
                self.logger.debug("Not expanding function macro %s", name)
                return False
            else:
                if self.files[-1].macro_expansions:
                    hideset = self.files[-1].macro_expansions[-1].hideset
                else:
                    hideset = set()
                hideset = hideset | {macro.name}

                if self.verbose:
                    self.logger.debug("%s expanded into %s", name, expansion)

                self.copy_leading_space(macro_token, expansion)
                self.push_expansion(MacroExpansion(iter(expansion), hideset))
                return True
        else:
            return False

    def expand_macro(self, macro, macro_token):
        """ Expand a single macro. """
        if isinstance(macro, FunctionMacro):  # Special macro:
            expansion = macro.function(macro_token)
        else:  # Normal macro:
            if macro.args is None:  # Macro without arguments
                expansion = macro.value
            else:  # This macro requires arguments
                token = self.next_token()
                if not token or token.typ != "(":
                    self.unget_token(token)
                    return
                args = self.gatherargs(macro)
                expansion = self.substitute_arguments(macro, args)

            expansion = self.concatenate(expansion)
        return expansion

    def copy_leading_space(self, macro_token, expansion):
        # Adjust token spacings of first token to adhere spacing of
        # the macro token:
        if expansion:
            expansion[0] = expansion[0].copy(
                first=macro_token.first, space=macro_token.space
            )

    def gatherargs(self, macro):
        """ Collect expanded arguments for macro """
        args, commas = self.parse_arguments()

        # Check amount of arguments:
        if macro.variadic:
            # macro.variadic, len(macro.args)
            req_args = len(macro.args)
            if len(args) < req_args:
                self.error(
                    "Macro {} got {} arguments ({})"
                    ", but required at least {}".format(
                        macro.name, len(args), args, req_args
                    )
                )

            # Split args:
            args, va_args_args = args[:req_args], args[req_args:]

            # Flatten comma's and arguments into single token sequence:
            va_args = []
            if va_args_args:
                va_args_commas = [None] + commas[req_args:]
                assert len(va_args_commas) == len(va_args_args)
                for comma, part in zip(va_args_commas, va_args_args):
                    if comma:
                        va_args.append(comma)
                    va_args.extend(part)

            # Append va_args as the last argument
            args.append(va_args)
        else:
            # Fixed parameter count macro.
            if len(macro.args) > 0:
                if len(args) != len(macro.args):
                    self.error(
                        "Macro {} got {} arguments, but expected {}".format(
                            macro.name, len(args), len(macro.args)
                        )
                    )
            else:
                assert len(args) > 0
                if args[0] or len(args) > 1:
                    self.error(
                        "Macro {} got unexpected arguments".format(macro.name)
                    )
                args = []

        self.normalize_space(args)
        return args

    def normalize_space(self, args):
        """ Normalize spaces in macro expansions.

        If we have space, it will be a single space.
        """
        for arg in args:
            for token in arg:
                if token.space:
                    token.space = " "

    def parse_arguments(self):
        """ Parse arguments for a function like macro.

        - Keep track of parenthesis level.
        """
        args = []
        commas = []
        parens = 1  # We already parsed the opening '('
        arg = []

        while parens > 0:
            token = self.next_token(expand=False)

            # Keep track of parenthesis level:
            if token.typ == "(":
                parens += 1
            elif token.typ == ")":
                parens -= 1

            if parens == 0:
                args.append(arg)
            elif token.typ == "," and parens == 1:
                # We have a complete argument, add it to the list:
                args.append(arg)
                arg = []
                # Add comma token to the list:
                commas.append(token)
            else:
                arg.append(token)

        assert len(args) == len(commas) + 1
        return args, commas

    def expand_token_sequence(self, tokens):
        """ Macro expand a sequence of tokens. """
        # Push a new file onto the file stack:
        filename = "<macro>"
        source_file = SourceFile(filename)
        macro_file = FileExpander(source_file, iter(tokens))
        self.files.append(macro_file)
        expansion = list(self.process_tokens())
        self.files.pop()
        return expansion

    def substitute_arguments(self, macro, args):
        """ Return macro contents with substituted arguments.

        Pay special care to # and ## operators, When an argument is used
        in # or ##, it is not macro expanded.
        """
        new_line = []
        # print(args)
        # expanded_args = [self.expand_token_sequence(a) for a in args]
        # Create two variants: expanded and not expanded:
        repl_map = {fp: a for fp, a in zip(macro.args, args)}

        # Spiffy variadic macro!
        if macro.variadic:
            repl_map["__VA_ARGS__"] = args[-1]

        # print(repl_map)
        if self.verbose:
            self.logger.debug("replacement map: %s", repl_map)
        sle = LineParser(macro.value)
        while not sle.at_end:
            token = sle.consume()
            if token.typ == "#":
                # Stringify operator '#'!
                # Use the unexpanded version for this one
                arg_name = sle.consume("ID")
                if arg_name.val in repl_map:
                    new_line.append(
                        self.stringify(
                            token, repl_map[arg_name.val], arg_name.loc
                        )
                    )
                else:
                    self.error(
                        "{} does not refer a macro argument".format(
                            arg_name.val
                        )
                    )
            elif token.typ == "ID" and token.val in repl_map:
                # TODO: maybe figure out a better way for this peaking at '##'
                replacement = repl_map[token.val]
                # Test use in '##' construction:
                used_in_concat = sle.previous == "##" or sle.peak == "##"
                if not used_in_concat:
                    # Do macro expansion on the argument:
                    replacement = self.expand_token_sequence(replacement)
                replacement = self.copy_tokens(replacement, token.space)
                new_line.extend(replacement)
            else:
                new_line.append(token)

        return new_line

    def copy_tokens(self, tokens, first_space):
        """ Copy a series of tokens.
        """
        new_line = []
        first = True
        for token in tokens:
            if first:
                rt2 = token.copy(space=first_space)
            else:
                rt2 = token.copy()
            new_line.append(rt2)
            first = False
        return new_line

    def stringify(self, hash_token, snippet, loc):
        """ Handle the '#' stringify operator.

        Take care of:
        - single space between the tokens being stringified
        - no spaces before first and after last token
        - escape double quotes of strings and backslash inside strings.
        """

        def escape(t):
            if t.typ in ["STRING", "CHAR"]:
                return t.val.replace("\\", "\\\\").replace('"', '\\"')
            else:
                return t.val

        string_value = '"{}"'.format(" ".join(map(escape, snippet)))
        return CToken("STRING", string_value, hash_token.space, False, loc)

    def concat(self, lhs, rhs):
        """ Concatenate two tokens """
        total_text = lhs.val + rhs.val

        # Invoke the lexer again on glued text to produce tokens:
        tokens = lex_text(total_text, self.coptions)
        if len(tokens) == 1:
            return tokens[0].copy(space=lhs.space, first=lhs.first)
        else:
            self.error('Invalidly glued "{}"'.format(total_text), loc=lhs.loc)

    def concatenate(self, tokens):
        """ Handle the '##' token concatenation operator """
        le = LineParser(tokens)
        glue_line = []
        while not le.at_end:
            lhs = le.consume()
            while le.has_consumed("##"):
                rhs = le.consume()
                lhs = self.concat(lhs, rhs)
            glue_line.append(lhs)
        return glue_line

    def make_newline_token(self, line):
        raise NotImplementedError()
        # return CToken('BOL', '', '', True, Location(line))

    # Handle directives
    def handle_directive(self, loc):
        """ Handle a single preprocessing directive """
        self.files[-1].in_directive = True
        if self.at_line_start:
            # Handle null directive:
            new_line_token = CToken("WS", "", "", True, loc)
            yield new_line_token
        else:
            directive_token = self.consume("ID")
            directive = directive_token.val
            if self.verbose:
                self.logger.debug("Handing #%s directive", directive)

            if directive == "ifdef":
                yield from self.handle_ifdef_directive(directive_token)
            elif directive == "ifndef":
                yield from self.handle_ifndef_directive(directive_token)
            elif directive == "if":
                yield from self.handle_if_directive(directive_token)
            elif directive == "elif":
                yield from self.handle_elif_directive(directive_token)
            elif directive == "else":
                yield from self.handle_else_directive(directive_token)
            elif directive == "endif":
                yield from self.handle_endif_directive(directive_token)
            elif directive == "include":
                yield from self.handle_include_directive(directive_token)
            elif directive == "include_next":
                yield from self.handle_include_next_directive(directive_token)
            elif directive == "define":
                yield from self.handle_define_directive(directive_token)
            elif directive == "undef":
                yield from self.handle_undef_directive(directive_token)
            elif directive == "line":
                yield from self.handle_line_directive(directive_token)
            elif directive == "error":
                yield from self.handle_error_directive(directive_token)
            elif directive == "warning":
                yield from self.handle_warning_directive(directive_token)
            elif directive == "pragma":
                yield from self.handle_warning_directive(directive_token)
            else:  # pragma: no cover
                self.error(
                    "not implemented: {}".format(directive),
                    loc=directive_token.loc,
                )
        self.files[-1].in_directive = False

    def skip_excluded_block(self):
        """ Skip the block excluded by if/ifdef.

        Skip tokens until we hit #endif or alike.
        """
        self.files[-1].in_directive = False
        nesting = 0
        while True:
            hash_token = self.next_token(expand=False)

            # Check end of file:
            if hash_token is None:
                self.error("Unterminated #if/#elif/#else block")

            # Check if we have a directive.
            if hash_token.first and hash_token.typ == "#":
                directive_token = self.next_token(expand=False)
                if directive_token.typ == "ID":
                    # Stop on else/elif/endif block:
                    if nesting == 0 and directive_token.val in [
                        "else",
                        "elif",
                        "endif",
                    ]:
                        self.unget_token(directive_token)
                        self.unget_token(hash_token)
                        break

                    # Handle nesting levels:
                    if directive_token.val in ["endif"]:
                        nesting -= 1
                    elif directive_token.val in ["if", "ifdef", "ifndef"]:
                        nesting += 1

            # Consume line in all cases:
            self.eat_line()

            # Construct empty line:
            new_line_token = CToken("WS", "", "", True, hash_token.loc)
            yield new_line_token

    def handle_ifdef_directive(self, directive_token):
        """ Handle an `#ifdef` directive. """
        test_define = self.consume("ID", expand=False).val
        condition = self.is_defined(test_define)
        new_line_token = CToken("WS", "", "", True, directive_token.loc)
        yield new_line_token
        yield from self.do_if(condition, directive_token.loc)

    def handle_ifndef_directive(self, directive_token):
        """ Handle an `#ifndef` directive. """
        test_define = self.consume("ID", expand=False).val
        condition = not self.is_defined(test_define)
        new_line_token = CToken("WS", "", "", True, directive_token.loc)
        yield new_line_token
        yield from self.do_if(condition, directive_token.loc)

    def handle_if_directive(self, directive_token):
        """ Process an `#if` directive. """
        condition = bool(self.eval_expr())
        new_line_token = CToken("WS", "", "", True, directive_token.loc)
        yield new_line_token
        yield from self.do_if(condition, directive_token.loc)

    def do_if(self, condition, location):
        """ Handle #if/#ifdef/#ifndef. """
        self.files[-1].if_stack.append(IfState(condition, location))
        if self.verbose:
            self.logger.debug(
                "If-stack is %s deep", len(self.files[-1].if_stack)
            )

        if not condition:
            yield from self.skip_excluded_block()

    def handle_elif_directive(self, directive_token):
        """ Process `#elif` directive. """
        if not self.files[-1].if_stack:
            self.error("#elif outside #if", loc=directive_token.loc)

        if self.files[-1].if_stack[-1].in_else:
            self.error("#elif after #else", loc=directive_token.loc)

        can_else = not self.files[-1].if_stack[-1].was_active
        condition = bool(self.eval_expr()) and can_else
        if condition:
            self.files[-1].if_stack[-1].was_active = True

        new_line_token = CToken("WS", "", "", True, directive_token.loc)
        yield new_line_token
        if not condition:
            yield from self.skip_excluded_block()

    def handle_else_directive(self, directive_token):
        """ Process the `#else` directive. """
        if not self.files[-1].if_stack:
            self.error("#else outside #if", loc=directive_token.loc)

        if self.files[-1].if_stack[-1].in_else:
            self.error("One else too much in #ifdef", loc=directive_token.loc)

        self.files[-1].if_stack[-1].in_else = True
        active = not self.files[-1].if_stack[-1].was_active
        new_line_token = CToken("WS", "", "", True, directive_token.loc)
        yield new_line_token
        if not active:
            yield from self.skip_excluded_block()

    def handle_endif_directive(self, directive_token):
        """ Process the `#endif` directive. """
        if not self.files[-1].if_stack:
            self.error("Mismatching #endif", loc=directive_token.loc)
        self.files[-1].if_stack.pop()
        new_line_token = CToken("WS", "", "", True, directive_token.loc)
        yield new_line_token

    def handle_include_directive(self, directive_token):
        """ Process the `#include` directive. """
        use_current_dir, include_filename = self.parse_included_filename()

        for token in self.include(
            include_filename,
            directive_token.loc,
            use_current_dir=use_current_dir,
        ):
            yield token

        yield LineInfo(
            directive_token.loc.row + 1,
            directive_token.loc.filename,
            flags=[LineInfo.FLAG_RETURN_FROM_INCLUDE],
        )

    def handle_include_next_directive(self, directive_token):
        """ Process the `#include_next` directive. """
        use_current_dir, include_filename = self.parse_included_filename()

        for token in self.include(
            include_filename,
            directive_token.loc,
            use_current_dir=use_current_dir,
            include_next=True,
        ):
            yield token

        yield LineInfo(
            directive_token.loc.row + 1,
            directive_token.loc.filename,
            flags=[LineInfo.FLAG_RETURN_FROM_INCLUDE],
        )

    def parse_included_filename(self):
        """ Parse filename after #include/#include_next """
        token = self.consume(("<", "STRING"))
        if token.typ == "<":
            use_current_dir = False
            # TODO: this is a bad way of getting the filename:
            filename = ""
            token = self.consume()
            while token.typ != ">":
                filename += str(token)
                token = self.consume()
            include_filename = filename
        else:
            use_current_dir = True
            include_filename = token.val[1:-1]
        return use_current_dir, include_filename

    def handle_define_directive(self, directive_token):
        """ Process `#define` directive. """
        name = self.consume("ID", expand=False)

        # Handle function like macros:
        variadic = False
        token = self.next_token(expand=False)
        if token:
            if token.typ == "(" and not token.space:
                args = []
                while True:
                    if self.token.typ == "...":
                        self.consume("...", expand=False)
                        variadic = True
                        break
                    elif self.token.typ == "ID":
                        args.append(self.consume("ID", expand=False).val)
                    else:
                        break

                    # Eat comma, and get other arguments
                    if self.has_consumed(",", expand=False):
                        continue
                    else:
                        break
                self.consume(")", expand=False)
            else:
                self.unget_token(token)
                args = None
        else:
            args = None

        # Grab the value of the macro:
        value = self.eat_line()

        if value:
            # Patch first token spaces:
            value[0] = value[0].copy(space="")
        value_txt = "".join(map(str, value))
        macro = Macro(name.val, value, args=args, variadic=variadic)
        if self.verbose:
            self.logger.debug("Defining %s=%s", name.val, value_txt)
        self.define(macro)
        new_line_token = CToken("WS", "", "", True, directive_token.loc)
        yield new_line_token

    def handle_undef_directive(self, directive_token):
        """ Process `#undef` directive. """
        name = self.consume("ID", expand=False).val
        self.undefine(name)
        new_line_token = CToken("WS", "", "", True, directive_token.loc)
        yield new_line_token

    def handle_line_directive(self, directive_token):
        """ Process `#line` directive. """
        # use line and filename information to adjust lexer:
        line = self.consume(typ="NUMBER").val
        self.files[-1].source_file.row = int(line) - 1

        filename_token = self.next_token()
        if filename_token:
            if filename_token.typ == "STRING":
                filename = filename_token.val[1:-1]
            else:
                self.error("Expected filename here", loc=filename_token.loc)
            self.files[-1].source_file.filename = filename

        new_line_token = CToken("WS", "", "", True, directive_token.loc)
        yield new_line_token

    def handle_error_directive(self, directive_token):
        """ Process `#error` directive. """
        message = self.tokens_to_string(self.eat_line())
        self.error(message, loc=directive_token.loc)
        new_line_token = CToken("WS", "", "", True, directive_token.loc)
        yield new_line_token

    def handle_warning_directive(self, directive_token):
        """ Process `#warning` directive. """
        message = self.tokens_to_string(self.eat_line())
        self.warning(message)
        new_line_token = CToken("WS", "", "", True, directive_token.loc)
        yield new_line_token

    def handle_pragma_directive(self, directive_token):
        """ Process `#pragma` directive. """
        # Pragma's must be handled, or ignored.
        message = self.tokens_to_string(self.eat_line())
        self.logger.warning("Ignoring pragma: %s", message)
        new_line_token = CToken("WS", "", "", True, directive_token.loc)
        yield new_line_token

    def tokens_to_string(self, tokens):
        """ Create a text from the given tokens """
        return "".join(map(str, tokens)).strip()

    # Expression parsing:
    def eval_expr(self):
        """ Evaluate an expression """
        ast_tree = self.parse_expression()
        return self._eval_tree(ast_tree)

    OP_MAP = {
        "*": (11, False, operator.mul),
        "/": (11, False, operator.floordiv),
        "%": (11, False, operator.mod),
        "+": (10, False, operator.add),
        "-": (10, False, operator.sub),
        "<<": (9, False, operator.lshift),
        ">>": (9, False, operator.rshift),
        "<": (8, False, lambda x, y: int(x < y)),
        ">": (8, False, lambda x, y: int(x > y)),
        "<=": (8, False, lambda x, y: int(x <= y)),
        ">=": (8, False, lambda x, y: int(x >= y)),
        "==": (7, False, lambda x, y: int(x == y)),
        "!=": (7, False, lambda x, y: int(x != y)),
        "&": (6, False, operator.and_),
        "^": (5, False, operator.xor),
        "|": (4, False, operator.or_),
        "&&": (3, False, lambda x, y: int(bool(x) and bool(y))),
        "||": (2, False, lambda x, y: int(bool(x) or bool(y))),
        "?": (1, True, None),
    }

    def parse_expression(self, priority=0):
        """ Parse an expression in an #if

        Idea taken from: https://github.com/shevek/jcpp/blob/master/
            src/main/java/org/anarres/cpp/Preprocessor.java
        """
        token = self.consume()

        if token.typ in ["!", "-", "~"]:
            op = token.typ
            a = self.parse_expression(11)
            lhs = expressions.UnaryOperator(
                op, a, self._int_type, True, token.loc
            )
        elif token.typ == "+":
            lhs = self.parse_expression(11)
        elif token.typ == "(":
            self.files[-1].paren_level += 1
            lhs = self.parse_expression()
            self.consume(")")
            self.files[-1].paren_level -= 1
        elif token.typ == "ID":
            name = token.val
            if name == "defined":
                # self.logger.debug('Checking for "defined"')
                if self.has_consumed("(", expand=False):
                    test_define = self.consume("ID", expand=False).val
                    self.consume(")", expand=False)
                else:
                    test_define = self.consume("ID", expand=False).val
                lhs = int(self.is_defined(test_define))
                if self.verbose:
                    self.logger.debug("Defined %s = %s", test_define, lhs)
            else:
                if self.verbose:
                    self.logger.warning('Attention: undefined "%s"', name)
                lhs = 0
            lhs = expressions.NumericLiteral(lhs, self._int_type, token.loc)
        elif token.typ == "NUMBER":
            lhs, _ = cnum(token.val)
            # TODO: check type specifier?
            lhs = expressions.NumericLiteral(lhs, self._int_type, token.loc)
        elif token.typ == "CHAR":
            lhs, _ = charval(replace_escape_codes(token.val))
            # TODO: check type specifier?
            lhs = expressions.NumericLiteral(lhs, self._int_type, token.loc)
        else:
            raise NotImplementedError(token.val)

        while True:
            # This would be the next operator:
            token = self.next_token()

            # Stop at end of line:
            if not token:
                break

            op = token.typ

            # Determine if the operator has a low enough priority:
            if self._binop_take(op, priority):
                op_prio = self.OP_MAP[op][0]
            else:
                self.unget_token(token)
                break

            if op == "?":
                # Eat middle part
                middle = self.parse_expression()
                self.consume(":")
            else:
                middle = None

            # We are go, eat the right hand side
            rhs = self.parse_expression(op_prio)

            if op in self.OP_MAP:
                func = self.OP_MAP[op][2]
                if func:
                    lhs = expressions.BinaryOperator(
                        lhs, op, rhs, self._int_type, True, token.loc
                    )
                elif op == "?":
                    lhs = expressions.TernaryOperator(
                        lhs, op, middle, rhs, self._int_type, True, token.loc
                    )
                    # middle if lhs != 0 else rhs
                else:  # pragma: no cover
                    raise NotImplementedError(op)
            else:  # pragma: no cover
                raise NotImplementedError(op)

        return lhs

    def _binop_take(self, op, priority: int) -> bool:
        """ Test if we must take the next operator. """
        if op in self.OP_MAP:
            op_prio, right_associative = self.OP_MAP[op][:2]
            left_associative = not right_associative
            if left_associative:
                return op_prio > priority
            else:
                return op_prio >= priority
        else:
            return False

    def _eval_tree(self, expr):
        """ Evaluate a parsed tree """
        if isinstance(expr, expressions.NumericLiteral):
            value = expr.value
        elif isinstance(expr, expressions.UnaryOperator):
            value = self._eval_tree(expr.a)
            if expr.op == "!":
                value = int(not bool(value))
            elif expr.op == "-":
                value = -value
            elif expr.op == "~":
                value = ~value
            else:  # pragma: no cover
                raise NotImplementedError(expr.op)
        elif isinstance(expr, expressions.BinaryOperator):
            if expr.op == "||":
                # Short circuit logic:
                value = self._eval_tree(expr.a)
                if not value:
                    value = self._eval_tree(expr.b)
                value = int(bool(value))
            elif expr.op == "&&":
                # Short circuit logic:
                value = self._eval_tree(expr.a)
                if value:
                    value = self._eval_tree(expr.b)
                value = int(bool(value))
            else:
                func = self.OP_MAP[expr.op][2]
                value = func(self._eval_tree(expr.a), self._eval_tree(expr.b))
        elif isinstance(expr, expressions.TernaryOperator):
            value = self._eval_tree(expr.a)
            if value:
                value = self._eval_tree(expr.b)
            else:
                value = self._eval_tree(expr.c)
        else:  # pragma: no cover
            raise NotImplementedError(str(expr))
        return value


class FileExpander:
    """ Per source or header file an expander class is created

    Contains:
    - An if-stack to keep track of if-else nesting levels
    - Contains another stack of macro expansions in progress.
      If a macro is encountered, its contents are pushed on this stack
      and processing continues over there.
    """

    def __init__(self, source_file, tokens):
        self.source_file = source_file
        self.dependencies = []  # List of dependent files.
        self.if_stack = []  # If-def stack
        self.token_buffer = []  # Token undo stack
        self.tokens = tokens  # Base context iterator.
        self.macro_expansions = []  # A stack of macro expansions
        self.in_directive = False
        self.paren_level = 0  # Nesting of parenthesis in #if expression.

    def __repr__(self):
        return "<File expander source={}, macro={}>".format(
            self.source_file, self.macro_expansions
        )

    @property
    def peek(self):
        token = None

        # First try buffer:
        if token is None and self.token_buffer:
            token = self.token_buffer[0]

        # Second option: expansion stack:
        if token is None:
            for macro_expansion in reversed(self.macro_expansions):
                if macro_expansion.peek is not None:
                    token = macro_expansion.peek
                    break

        # Finally, base context:
        if token is None:
            token = next(self.tokens, None)
            if token is not None:
                self.unget(token)

        # Inside directives, newline tokens mean end of input:
        if self.in_directive and self.paren_level == 0:
            if token and token.first:
                token = None

        return token

    def next_token(self):
        """ Take next token from macro or base context. """
        # Start with no token:
        token = None

        # Try token buffer:
        if self.token_buffer:
            token = self.token_buffer.pop(0)

        # Try expansion stack:
        while token is None and self.macro_expansions:
            if self.macro_expansions[-1].peek is None:
                # We are at end of expansion
                self.macro_expansions.pop()
            else:
                token = self.macro_expansions[-1].next_token()
                break

        # Try base context:
        if token is None:
            token = next(self.tokens, None)

        # Check if we are in a directive:
        if self.in_directive and self.paren_level == 0:
            if token and token.first:
                # Inside directives, newline tokens mean end of line.
                self.unget(token)
                token = None

        return token

    def unget(self, token):
        self.token_buffer.insert(0, token)


class MacroExpansion:
    """ Macro expansion.

    Contains:
    - a token iterator (tokens)
    - a hideset
    """

    def __init__(self, tokens, hideset):
        self.tokens = tokens
        self.token_buffer = []
        self.hideset = hideset

    @property
    def peek(self):
        """ Take a sneak peek at the next token. """
        if not self.token_buffer:
            self.token_buffer.append(next(self.tokens, None))
        return self.token_buffer[0]

    def next_token(self):
        """ Pop the next token into picture. """
        if self.token_buffer:
            return self.token_buffer.pop(0)
        else:
            return next(self.tokens, None)

    def unget(self, token):
        """ Push back a single token. """
        self.token_buffer.insert(0, token)


class LineEater:
    """ This class processes a sequence of tokens one by one """

    logger = logging.getLogger("preprocessor")

    def __init__(self, line):
        self.line = line
        self.tokens = iter(line)
        self.token = None
        self._prev_token = None
        self._current_token = None
        self.next_token()

    def __str__(self):
        return "Ctx({})".format("".join(map(str, self.line)))

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


class LineParser(LineEater):
    def consume(self, typ=None):
        if not typ:
            if not self.peak:
                self.error("Expecting extra tokens")
            else:
                typ = self.peak

        if self.peak != typ:
            self.error("Expected {} but got {}".format(typ, self.peak))

        return self.next_token()

    def has_consumed(self, typ):
        if self.peak == typ:
            self.consume(typ)
            return True
        return False


class IfState:
    """ If status for use on the if-stack """

    def __init__(self, active, location):
        self.was_active = active
        self.location = location
        self.in_else = False  # Indicator whether we are in the else clause.

    def __str__(self):
        return "If-state(loc={})".format(self.location)


def skip_ws(tokens):
    """ Filter whitespace tokens """
    for token in tokens:
        if isinstance(token, LineInfo):
            pass
        elif token.typ in ["WS", "BOL"]:
            pass
        else:
            yield token


def string_convert(tokens):
    """ Phase 5 of compilation.

    Tasks:
    - Strip quotes.
    - Process escaped string constants into unicode.
    """

    for token in tokens:
        # Strip double quotes from string:
        if token.typ == "STRING":
            token.val = token.val[1:-1]

        if token.typ in ["STRING", "CHAR"]:
            token.val = replace_escape_codes(token.val)

        yield token


def string_concat(tokens):
    """ Merge adjacent string literals into single tokens.

    This is phase 6 of compilation. """
    string_token = None
    for token in tokens:
        if token.typ == "STRING":
            if string_token:
                string_token.val = string_token.val + token.val
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
        if token.typ == "ID":
            if token.val in keywords:
                token.typ = token.val
            yield token
        else:
            yield token

from .lexer import Lexer
from . import nodes


class Parser:
    """
        C Parser. implemented in a recursive descent way, like the CLANG[1]
        frontend for llvm, also without the lexer hack[2]. See for the gcc
        c parser code [3].

        The clang parser is very versatile, it can handle C, C++, objective C
        and also do code completion. This one is very simple, it can only
        parse C.

        [1] http://clang.org/
        [2] https://en.wikipedia.org/wiki/The_lexer_hack
        [3] https://raw.githubusercontent.com/gcc-mirror/gcc/master/gcc/c/
            c-parser.c
    """
    def __init__(self):
        self.lexer = Lexer()
        self.token = None

    def parse(self, src):
        """ Here the parsing of C is begun ... """
        self.tokens = self.lexer.lex(src)
        self.token = None
        self.next_token()
        unit = self.parse_translation_unit()
        return unit

    def consume(self, typ=None):
        """ Consume a token certain type """
        if typ is None:
            typ = self.peak
        assert typ == self.peak
        return self.next_token()

    def has_consumed(self, typ):
        """ Try to consume a certain token type """
        if self.peak == typ:
            self.consume(typ)
            return True
        else:
            return False

    @property
    def peak(self):
        return self.token.typ

    def next_token(self):
        """ Advance to the next token """
        tok = self.token
        # print(tok)
        if not tok or tok.typ != 'EOF':
            self.token = self.tokens.__next__()
            # Implement lexer hack here:
            symbol_table = set()
            if self.token.typ == 'ID':
                if self.token.val in symbol_table:
                    self.token.typ = 'TYPE-SPEC'
        return tok

    def parse_translation_unit(self):
        """ Top level begin """
        decls = []
        while self.peak != 'EOF':
            df = self.parse_external_declaration()
            decls.append(df)
        return nodes.Cu(decls)

    # Declarations part:
    def parse_external_declaration(self):
        return self.parse_function_or_object_decl()

    def parse_function_or_object_decl(self):
        """ Parse a function definition or a list of object declarations """
        ds = self.parse_decl_spec()
        # print(ds)
        return self.parse_decl_group(ds)

    def parse_declaration(self):
        """ Parse normal declaration inside function """
        ds = self.parse_decl_spec()
        # print(ds)
        # TODO: perhaps not parse functions here?
        return self.parse_decl_group(ds)

    def parse_decl_spec(self):
        """ Parse declaration stuff like, static, volatile, int, void, etc.."""
        ds = nodes.DeclSpec()
        while True:
            if self.peak in ['int', 'void', 'char', 'float']:
                typ = self.consume()
                if ds.has_type():
                    raise SyntaxError('TODO, proper error')
                else:
                    ds.typ = typ.typ
            elif self.peak in ['typedef', 'static', 'extern']:
                storage = self.consume().val
                ds.modifiers.append(storage)
            else:
                break
        return ds

    def parse_decl_group(self, ds):
        """ Parse the rest after the first declaration spec. For example
            we have parsed 'static int' and we will now parse the rest.
            This can be either a function, or a sequence of initializable
            variables. At least it will probably contain some sort of
            identifier and an optional pointer stuff.
        """
        d = self.parse_declarator()
        if d.is_function and not self.is_decl_following():
            # if function, parse implementation.
            self.parse_compound_statement()
            func_def = None
            return func_def

        # print(ds, d)
        while self.has_consumed(','):
            d = self.parse_declarator()
            # print(ds, d)
        self.consume(';')

    def is_decl_following(self):
        if self.peak in [',', ';', '=']:
            return True
        return False

    def parse_declarator(self):
        if self.peak == '*':
            # TODO: implement pointer fu here!
            raise NotImplementedError()
        return self.parse_direct_declarator()

    def parse_direct_declarator(self):
        # First parse some id, or something else
        d = nodes.Decl()
        if self.peak == 'ID':
            name = self.consume('ID')
            d.name = name.val
        elif self.peak == '(':
            raise NotImplementedError('special case?')
            self.consume('(')
            self.parse_declarator()
            self.consume(')')
        else:
            raise NotImplementedError(str(self.peak))

        # Now we have name, check for function decl:
        while True:
            if self.peak == '(':
                self.parse_function_declarator(d)
                d.f = True
            else:
                break
        return d

    def parse_function_declarator(self, d):
        """ Parse function postfix. We have type and name, now parse
            function arguments """
        # TODO: allow K&R style arguments
        args = []
        self.consume('(')
        if self.peak == ')':
            # No arguments..
            self.consume(')')
            return
        while True:
            ds = self.parse_decl_spec()
            d = self.parse_declarator()
            args.append(d)
            if not self.has_consumed(','):
                break
        self.consume(')')
        return args

    def parse_function_definition(self):
        """ Parse a function """
        raise NotImplementedError()
        self.parse_compound_statement()

    # Statement part:
    def parse_statement_or_declaration(self):
        """ Parse either a statement or a declaration """
        m = {
            'for': self.parse_for_statement,
            'if': self.parse_if_statement,
            'do': self.parse_do_statement,
            'while': self.parse_while_statement,
            'switch': self.parse_switch_statement,
            'case': self.parse_case_statement,
            'break': self.parse_break_statement,
            }
        if self.peak in m:
            stm = m[self.peak]()
        else:
            # The statement was not identifiable with a keyword.
            # We must now choose between an expression statement or a
            # declaration...
            if self.is_declaration_statement():
                stm = self.parse_declaration()
                return stm
            else:
                stm = self.parse_expression_statement()
        self.consume(';')
        return stm

    def is_declaration_statement(self):
        """ Determine whether we are facing a declaration or not """
        if self.peak in ['int', 'void', 'char', 'float']:
            return True
        if self.peak in ['static', 'volatile']:
            return True
        if self.peak == 'ID':
            # Check for defined type here
            # TODO
            # raise NotImplementedError()
            return False
        return False

    def parse_statement(self):
        """ Parse a statement """
        return self.parse_statement_or_declaration()

    def parse_expression_statement(self):
        """ Parse an expression statement """
        self.parse_expression()

    def parse_compound_statement(self):
        self.consume('{')
        while self.peak != '}':
            self.parse_statement_or_declaration()
        self.consume('}')

    def parse_if_statement(self):
        """ Parse an if statement """
        self.consume('if')
        self.consume('(')
        condition = self.parse_expression()
        self.consume(')')
        yes = self.parse_statement()
        if self.has_consumed('else'):
            no = self.parse_statement()
        else:
            no = nodes.Empty()
        return nodes.If(condition, yes, no)

    def parse_switch_statement(self):
        """ Parse an switch statement """
        self.consume('switch')
        self.consume('(')
        condition = self.parse_expression()
        self.consume(')')
        body = self.parse_statement()
        return nodes.Switch(condition, body)

    def parse_case_statement(self):
        """ Parse a case """
        self.consume('case')
        self.parse_expression()
        self.consume(':')

    def parse_break_statement(self):
        """ Parse a break """
        self.consume('break')

    def parse_while_statement(self):
        """ Parse a while statement """
        self.consume('while')
        self.consume('(')
        condition = self.parse_expression()
        self.consume(')')
        self.parse_statement()
        return nodes.While(condition)

    def parse_do_statement(self):
        """ Parse a do-while statement """
        loc = self.consume('do').loc
        body = self.parse_statement()
        self.consume('while')
        self.consume('(')
        condition = self.parse_expression()
        self.consume(')')
        self.parse_statement()
        return nodes.DoWhile(body, condition, loc)

    def parse_for_statement(self):
        """ Parse a for statement """
        loc = self.consume('for').loc
        self.consume('(')
        condition = self.parse_expression()
        self.consume(';')
        self.parse_expression()
        self.consume(';')
        self.parse_expression()
        self.consume(')')
        body = self.parse_statement()
        return nodes.ForStatement(condition, body, loc)

    # Expression parts:
    def parse_expression(self):
        """ Parse an expression """
        return self.parse_assignment_expression()

    def parse_assignment_expression(self):
        return self.parse_binop_with_precedence(0)

    def parse_cast_expression(self):
        pass

    def parse_binop_with_precedence(self, prio):
        lhs = self.parse_primary_expression()
        prio_map = {
            '=': 0,
            '+': 50,
            '-': 50,
            '*': 80,
            '>>': 100,
        }
        # print('prio=', prio, self.peak)
        while self.peak in prio_map and prio_map[self.peak] >= prio:
            op = self.consume()
            prio2 = prio_map[op.val]
            if op.val == '=':
                prio2 += 0
            else:
                prio2 += 1
            rhs = self.parse_binop_with_precedence(prio2)
            lhs = nodes.Binop(lhs, op.val, rhs, op.loc)
            #print(lhs)
        return lhs

    def parse_primary_expression(self):
        """ Parse a primary expression """
        if self.peak == 'ID':
            i = self.consume()
            return i.val
        elif self.peak == 'NUMBER':
            n = self.consume()
            return n.val
        else:
            raise NotImplementedError(str(self.peak))

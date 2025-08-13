"""This module contains the parsing parts for the c3 language."""

import logging
from ...common import CompilerError
from ..tools.recursivedescent import RecursiveDescentParser
from . import astnodes as ast
from .scope import Scope


class Parser(RecursiveDescentParser):
    """Parses sourcecode into an abstract syntax tree (AST)"""

    logger = logging.getLogger("c3")

    def __init__(self, diag):
        super().__init__()
        self.diag = diag
        self.current_scope = None
        self.mod = None

    def parse_source(self, tokens, context):
        """Parse a module from tokens"""
        self.logger.debug("Parsing source")
        self.init_lexer(tokens)
        try:
            module = self.parse_module(context)
            self.logger.debug("Parsing complete")
        except CompilerError as ex:
            self.diag.add_diag(ex)
            raise
        return module

    def add_symbol(self, sym):
        """Add a symbol to the current scope"""
        if self.current_scope.has_symbol(sym.name, include_parent=False):
            self.error(f"Redefinition of {sym.name}", loc=sym.loc)
        else:
            self.current_scope.add_symbol(sym)

    def parse_module(self, context):
        """Parse a module definition"""
        self.consume("module")
        name = self.consume("ID")
        self.consume(";")
        self.logger.debug("Parsing package %s", name.val)
        self.mod = context.get_module(name.val)
        self.current_scope = self.mod.inner_scope
        while self.peek != "EOF":
            self.parse_top_level()
        self.consume("EOF")
        return self.mod

    def parse_top_level(self):
        """Parse toplevel declaration"""
        # Handle public specifier:
        public = self.has_consumed("public")

        # Handle a toplevel construct
        if self.peek == "function":
            self.parse_function_def(public=public)
        elif self.peek == "var":
            self.parse_variable_def()
        elif self.peek == "const":
            self.parse_const_def()
        elif self.peek == "type":
            self.parse_type_def(public=public)
        elif self.peek == "import" and not public:
            self.parse_import()
        else:
            self.error("Expected function, var, const or type", self.token.loc)

    def parse_import(self):
        """Parse import construct"""
        self.consume("import")
        name = self.consume("ID").val
        self.mod.imports.append(name)
        self.consume(";")

    def parse_designator(self):
        """A designator designates an object with a name."""
        name = self.consume("ID")
        return ast.Identifier(name.val, self.current_scope, name.loc)

    def parse_id_sequence(self):
        """Parse a sequence of id's"""
        ids = [self.consume("ID")]
        while self.has_consumed(","):
            ids.append(self.consume("ID"))
        return ids

    # Type system
    def parse_type_spec(self):
        """Parse type specification. Type specs are read from right to left.

        A variable spec is given by:
        var [typeSpec] [modifiers] [pointer/array suffix] variable_name

        For example:
        var int volatile * ptr;
        creates a pointer to a volatile integer.
        """
        # Parse the first part of a type spec:
        if self.peek == "struct":
            self.consume("struct")
            self.consume("{")
            mems = []
            while self.peek != "}":
                mem_t = self.parse_type_spec()
                for i in self.parse_id_sequence():
                    mems.append(ast.StructField(i.val, mem_t))
                self.consume(";")
            self.consume("}")
            the_type = ast.StructureType(mems)
        elif self.peek == "enum":
            raise NotImplementedError("enum not yet implemented")
        else:
            # The type is identified by an identifier:
            the_type = self.parse_designator()
            while self.has_consumed("."):
                field = self.consume("ID")
                the_type = ast.Member(the_type, field.val, field.loc)

        # Check for the volatile modifier (this is a suffix):
        the_type.volatile = self.has_consumed("volatile")

        # Check for pointer or array suffix:
        while self.peek in ["*", "["]:
            if self.has_consumed("*"):
                the_type = ast.PointerType(the_type)
            elif self.has_consumed("["):
                size = self.parse_expression()
                self.consume("]")
                the_type = ast.ArrayType(the_type, size)
            else:  # pragma: no cover
                raise RuntimeError()

            # Check (again) for the volatile modifier:
            the_type.volatile = self.has_consumed("volatile")
        return the_type

    def parse_type_def(self, public=True):
        """Parse a type definition"""
        self.consume("type")
        newtype = self.parse_type_spec()
        typename = self.consume("ID")
        self.consume(";")
        typedef = ast.DefinedType(typename.val, newtype, public, typename.loc)
        self.add_symbol(typedef)

    def parse_variable_def(self, public=True):
        """Parse variable declaration, optionally with initialization."""
        self.consume("var")
        var_type = self.parse_type_spec()
        variables = []
        while True:
            name = self.consume("ID")
            var = ast.Variable(name.val, var_type, public, name.loc)
            # Munch initial value:
            if self.peek == "=":
                self.consume("=")
                var.ival = self.parse_const_expression()
            self.add_symbol(var)
            variables.append(var)
            if not self.has_consumed(","):
                break
        self.consume(";")
        return variables

    def parse_const_def(self):
        """Parse a constant definition"""
        self.consume("const")
        typ = self.parse_type_spec()
        while True:
            name = self.consume("ID")
            self.consume("=")
            val = self.parse_expression()
            constant = ast.Constant(name.val, typ, val, name.loc)
            self.add_symbol(constant)
            if not self.has_consumed(","):
                break
        self.consume(";")

    def parse_function_def(self, public=True):
        """Parse function definition"""
        loc = self.consume("function").loc
        returntype = self.parse_type_spec()
        fname = self.consume("ID").val
        self.logger.debug("Parsing function %s", fname)
        func = ast.Function(fname, public, loc)
        self.add_symbol(func)
        func.inner_scope = Scope(self.current_scope)
        func.package = self.mod
        self.current_scope = func.inner_scope
        self.consume("(")
        parameters = []
        if not self.has_consumed(")"):
            while True:
                typ = self.parse_type_spec()
                name = self.consume("ID")
                param = ast.FormalParameter(name.val, typ, name.loc)
                self.add_symbol(param)
                parameters.append(param)
                if not self.has_consumed(","):
                    break
            self.consume(")")
        paramtypes = [p.typ for p in parameters]
        func.typ = ast.FunctionType(paramtypes, returntype)
        func.parameters = parameters
        if self.has_consumed(";"):
            func.body = None
        else:
            func.body = self.parse_compound()
        self.current_scope = self.current_scope.parent

    def parse_if(self):
        """Parse if statement"""
        loc = self.consume("if").loc
        self.consume("(")
        condition = self.parse_expression()
        self.consume(")")
        true_code = self.parse_statement()
        if self.has_consumed("else"):
            false_code = self.parse_statement()
        else:
            false_code = ast.Empty()
        return ast.If(condition, true_code, false_code, loc)

    def parse_switch(self) -> ast.Switch:
        """Parse switch statement"""
        loc = self.consume("switch").loc
        self.consume("(")
        expression = self.parse_expression()
        self.consume(")")
        options = []
        self.consume("{")
        while self.peek != "}":
            case_kw = self.consume(["case", "default"])
            if case_kw.typ == "case":
                value = self.parse_expression()
            else:
                value = None
            self.consume(":")
            statement = self.parse_statement()
            options.append((value, statement))
        self.consume("}")
        return ast.Switch(expression, options, loc)

    def parse_while(self) -> ast.While:
        """Parses a while statement"""
        loc = self.consume("while").loc
        self.consume("(")
        condition = self.parse_expression()
        self.consume(")")
        statements = self.parse_statement()
        return ast.While(condition, statements, loc)

    def parse_for(self) -> ast.For:
        """Parse a for statement"""
        loc = self.consume("for").loc
        self.consume("(")
        init = self.parse_statement()
        self.consume(";")
        condition = self.parse_expression()
        self.consume(";")
        final = self.parse_statement()
        self.consume(")")
        statements = self.parse_statement()
        return ast.For(init, condition, final, statements, loc)

    def parse_return(self) -> ast.Return:
        """Parse a return statement"""
        loc = self.consume("return").loc
        if self.has_consumed(";"):
            return ast.Return(None, loc)
        else:
            expr = self.parse_expression()
            self.consume(";")
            return ast.Return(expr, loc)

    def parse_compound(self):
        """Parse a compound statement, which is bounded by '{' and '}'"""
        loc = self.consume("{").loc
        statements = []
        while self.peek != "}":
            statements.append(self.parse_statement())
        self.consume("}")

        # Enforce styling:
        # if cb1.loc.col != cb2.loc.col:
        #    self.error('Braces not in same column!')

        return ast.Compound(statements, loc)

    def parse_statement(self) -> ast.Statement:
        """Determine statement type based on the pending token"""
        mapping = {
            "if": self.parse_if,
            "while": self.parse_while,
            "for": self.parse_for,
            "switch": self.parse_switch,
            "return": self.parse_return,
            "{": self.parse_compound,
        }
        if self.peek in mapping:
            return mapping[self.peek]()
        elif self.has_consumed(";"):
            return ast.Empty()
        elif self.peek == "var":
            variables = self.parse_variable_def()
            statements = [ast.VariableDeclaration(v, v.loc) for v in variables]
            loc = variables[0].loc
            return ast.Compound(statements, loc)
        else:
            expression = self.parse_unary_expression()
            if self.peek in ast.Assignment.operators:
                # We enter assignment mode here.
                operator = self.peek
                loc = self.consume(operator).loc
                rhs = self.parse_expression()
                return ast.Assignment(expression, rhs, loc, operator)
            else:
                # Must be call statement!
                return ast.ExpressionStatement(expression, expression.loc)

    LEFT_ASSOCIATIVITY = 1
    op_binding_powers = {
        "or": (10, LEFT_ASSOCIATIVITY),
        "and": (20, LEFT_ASSOCIATIVITY),
        "==": (30, LEFT_ASSOCIATIVITY),
        "<": (30, LEFT_ASSOCIATIVITY),
        ">": (30, LEFT_ASSOCIATIVITY),
        "<=": (30, LEFT_ASSOCIATIVITY),
        ">=": (30, LEFT_ASSOCIATIVITY),
        "!=": (30, LEFT_ASSOCIATIVITY),
        "<<": (40, LEFT_ASSOCIATIVITY),
        ">>": (40, LEFT_ASSOCIATIVITY),
        "+": (50, LEFT_ASSOCIATIVITY),
        "-": (50, LEFT_ASSOCIATIVITY),
        "*": (60, LEFT_ASSOCIATIVITY),
        "/": (60, LEFT_ASSOCIATIVITY),
        "%": (60, LEFT_ASSOCIATIVITY),
        "|": (70, LEFT_ASSOCIATIVITY),
        "&": (80, LEFT_ASSOCIATIVITY),
        "^": (80, LEFT_ASSOCIATIVITY),
    }

    def parse_const_expression(self):
        """Parse array initializers and other constant values"""
        if self.peek == "{":
            loc = self.consume("{").loc
            elements = []
            if self.peek == ".":
                self.consume(".")
                field = self.consume("ID").val
                self.consume("=")
                expr = self.parse_const_expression()
                elements.append((field, expr))
                while self.has_consumed(","):
                    self.consume(".")
                    field = self.consume("ID").val
                    self.consume("=")
                    expr = self.parse_const_expression()
                    elements.append((field, expr))
                self.consume("}")
                return ast.NamedExpressionList(elements, loc)
            else:
                elements.append(self.parse_const_expression())
                while self.has_consumed(","):
                    elements.append(self.parse_const_expression())
                self.consume("}")
                return ast.ExpressionList(elements, loc)
        else:
            return self.parse_expression()

    def parse_expression(self, rbp=0) -> ast.Expression:
        """Process expressions with precedence climbing.

        See also:

        http://eli.thegreenplace.net/2012/08/02/
        parsing-expressions-by-precedence-climbing
        """
        lhs = self.parse_cast_expression()
        while (
            self.peek in self.op_binding_powers
            and self.op_binding_powers[self.peek][0] >= rbp
        ):
            operator = self.next_token()
            precedence, associativity = self.op_binding_powers[operator.typ]
            if associativity == self.LEFT_ASSOCIATIVITY:
                next_precedence = precedence + 1
            else:  # pragma: no cover
                next_precedence = precedence
            rhs = self.parse_expression(next_precedence)
            lhs = ast.Binop(lhs, operator.typ, rhs, operator.loc)
        return lhs

    # Domain of unary expressions:

    def parse_cast_expression(self) -> ast.Expression:
        """Parse a cast expression.

        The C-style type cast conflicts with '(' expr ')'
        so introduce extra keyword 'cast'.
        """
        if self.peek == "cast":
            loc = self.consume("cast").loc
            self.consume("<")
            to_type = self.parse_type_spec()
            self.consume(">")
            self.consume("(")
            inner_expression = self.parse_expression()
            self.consume(")")
            return ast.TypeCast(to_type, inner_expression, loc)
        elif self.peek == "sizeof":
            # Compiler internal function to determine size of a type
            loc = self.consume("sizeof").loc
            self.consume("(")
            typ = self.parse_type_spec()
            self.consume(")")
            return ast.Sizeof(typ, loc)
        else:
            return self.parse_unary_expression()

    def parse_unary_expression(self):
        """Handle unary plus, minus and pointer magic"""
        if self.peek in ["&", "*", "-", "+", "not"]:
            operation = self.next_token()
            inner_expression = self.parse_cast_expression()
            if operation.val == "*":
                return ast.Deref(inner_expression, operation.loc)
            else:
                return ast.Unop(operation.typ, inner_expression, operation.loc)
        else:
            return self.parse_postfix_expression()

    def parse_postfix_expression(self) -> ast.Expression:
        """Parse postfix expression"""
        pfe = self.parse_primary_expression()
        while self.peek in ["[", ".", "->", "("]:
            if self.has_consumed("["):
                i = self.parse_expression()
                self.consume("]")
                pfe = ast.Index(pfe, i, i.loc)
            elif self.has_consumed("->"):
                field = self.consume("ID")
                pfe = ast.Deref(pfe, pfe.loc)
                pfe = ast.Member(pfe, field.val, field.loc)
            elif self.has_consumed("."):
                field = self.consume("ID")
                pfe = ast.Member(pfe, field.val, field.loc)
            elif self.has_consumed("("):
                # Function call
                args = []
                if not self.has_consumed(")"):
                    args.append(self.parse_expression())
                    while self.has_consumed(","):
                        args.append(self.parse_expression())
                    self.consume(")")
                pfe = ast.FunctionCall(pfe, args, pfe.loc)
            else:  # pragma: no cover
                raise RuntimeError()
        return pfe

    def parse_primary_expression(self) -> ast.Expression:
        """Literal and parenthesis expression parsing"""
        tok = self.next_token()
        if tok.typ == "(":
            expr = self.parse_expression()
            self.consume(")")
        elif tok.typ == "NUMBER":
            expr = ast.Literal(tok.val, tok.loc)
        elif tok.typ == "REAL":
            expr = ast.Literal(tok.val, tok.loc)
        elif tok.typ == "true":
            expr = ast.Literal(True, tok.loc)
        elif tok.typ == "false":
            expr = ast.Literal(False, tok.loc)
        elif tok.typ == "STRING":
            expr = ast.Literal(tok.val, tok.loc)
        elif tok.typ == "ID":
            self.backup_token(tok)
            expr = self.parse_designator()
        else:
            self.error(f"Expected NUM, ID or (expr), got {tok.typ}", tok.loc)
        return expr

import io
import unittest
try:
    # Use mock library for assert_called method
    import mock
except:
    from unittest import mock


from ppci.lang.c import CLexer, lexer, CParser, CSemantics
from ppci.lang.c.preprocessor import prepare_for_parsing
from ppci.lang.c.options import COptions


def gen_tokens(tokens):
    """ Helper function which creates a token iterator """
    for col, token in enumerate(tokens, start=1):
        typ, val = token
        loc = lexer.SourceLocation('test.c', 1, col, 1)
        yield lexer.CToken(typ, val, '', False, loc)


class CParserTestCase(unittest.TestCase):
    """ Test the C parser.

    Since the C parser uses the C semantics class, we use a mock for
    the semantics and assert that the proper functions are called on it.
    """
    def setUp(self):
        coptions = COptions()
        self.semantics = mock.Mock(spec=CSemantics, name='semantics')
        self.parser = CParser(coptions, self.semantics)

    def parse(self, tokens):
        cu = self.parser.parse(gen_tokens(tokens))
        return cu

    def given_tokens(self, tokens):
        """ Provide the parser with the given tokens """
        self.parser.init_lexer(gen_tokens(tokens))

    def given_source(self, source):
        """ Lex a given source and prepare the parser """
        clexer = CLexer(COptions())
        f = io.StringIO(source)
        tokens = clexer.lex(f, '<snippet>')
        tokens = prepare_for_parsing(tokens, self.parser.keywords)
        self.parser.init_lexer(tokens)

    def test_empty(self):
        """ Test the obvious empty case! """
        cu = self.parse([])
        self.assertSequenceEqual(
            [
                mock.call.begin(),
                mock.call.finish_compilation_unit()
            ],
            self.semantics.mock_calls
        )

    def test_global_int(self):
        """ Test the parsing of a global integer """
        tokens = [('int', 'int'), ('ID', 'A'), (';', ';')]
        cu = self.parse(tokens)
        # TODO: this would be nice, but is very hard as of now:
        # self.semantics.on_variable_declaration.assert_called_with(
        #    None, None, 'A', [],
        #    ('test1.c', 1, 2)
        # )
        self.semantics.on_variable_declaration.assert_called()
        self.semantics.add_global_declaration.assert_called()

    def test_function(self):
        """ Test the parsing of a function """
        tokens = [
            ('int', 'int'), ('ID', 'add'), ('(', '('), ('int', 'int'),
            ('ID', 'x'), (',', ','), ('int', 'int'), ('ID', 'y'), (')', ')'),
            ('{', '{'), ('return', 'return'), ('ID', 'x'), ('+', '+'),
            ('ID', 'y'), (';', ';'), ('}', '}')]
        cu = self.parse(tokens)
        self.semantics.add_global_declaration.assert_called()
        self.semantics.on_binop.assert_called()
        self.semantics.on_return.assert_called()

    def test_pointer_declaration(self):
        """ Test the proper parsing of a pointer to an integer """
        self.given_source('int *a;')
        declarations = self.parser.parse_declarations()
        self.semantics.on_variable_declaration.assert_called()

    def test_cdecl_example1(self):
        """ Test the proper parsing of 'int (*(*foo)(void))[3]'.

        Example taken from cdecl.org.
        """
        src = 'int (*(*foo)(void))[3];'
        self.given_source(src)
        declarations = self.parser.parse_declarations()
        self.semantics.on_variable_declaration.assert_called()

    def test_function_returning_pointer(self):
        """ Test the proper parsing of a pointer to a function """
        self.given_source('int *a(int x);')
        declarations = self.parser.parse_declarations()
        self.semantics.on_variable_declaration.assert_called()

    def test_function_pointer(self):
        """ Test the proper parsing of a pointer to a function """
        self.given_source('int (*a)(int x);')
        declarations = self.parser.parse_declarations()
        self.semantics.on_variable_declaration.assert_called()

    def test_array_pointer(self):
        """ Test the proper parsing of a pointer to an array """
        self.given_source('int (*a)[3];')
        declarations = self.parser.parse_declarations()
        self.semantics.on_variable_declaration.assert_called()

    def test_struct_declaration(self):
        """ Test struct declaration parsing """
        self.given_source('struct {int g; } a;')
        declarations = self.parser.parse_declarations()
        self.semantics.on_struct_or_union.assert_called()
        self.semantics.on_variable_declaration.assert_called()

    def test_union_declaration(self):
        """ Test union declaration parsing """
        self.given_source('union {int g; } a;')
        declarations = self.parser.parse_declarations()
        self.semantics.on_struct_or_union.assert_called()
        self.semantics.on_variable_declaration.assert_called()

    def test_expression_precedence(self):
        self.given_source('*l==*r && *l')
        expr = self.parser.parse_expression()
        self.semantics.on_binop.assert_called()
        self.semantics.on_unop.assert_called()

    def test_expression_precedence_comma_casting(self):
        self.semantics.on_cast.side_effect = ['cast']
        self.semantics.on_number.side_effect = [1, 2]
        self.semantics.on_binop.side_effect = [',']
        self.given_source('(int)1,2')
        expr = self.parser.parse_expression()
        # TODO: assert precedence in some clever way
        self.semantics.on_binop.assert_called()
        self.semantics.on_cast.assert_called()

    def test_ternary_expression_precedence_case1(self):
        self.given_source('a ? b ? c : d : e')
        expr = self.parser.parse_expression()
        self.assertEqual(5, self.semantics.on_variable_access.call_count)
        self.assertEqual(2, self.semantics.on_ternop.call_count)

    def test_ternary_expression_precedence_case2(self):
        self.given_source('a ? b : c ? d : e')
        expr = self.parser.parse_expression()
        self.assertEqual(5, self.semantics.on_variable_access.call_count)
        self.assertEqual(2, self.semantics.on_ternop.call_count)


if __name__ == '__main__':
    unittest.main()

import unittest
import io
import os
from ppci.common import CompilerError
from ppci.lang.c import CBuilder, CLexer, lexer, CParser, nodes
from ppci.lang.c import CContext
from ppci.lang.c.preprocessor import CTokenPrinter, prepare_for_parsing
from ppci.lang.c.options import COptions
from ppci.lang.c.castxml import CastXmlReader
from ppci.lang.c.utils import cnum
from ppci.arch.example import ExampleArch
from ppci import ir
from ppci.irutils import Verifier


testdir = os.path.dirname(os.path.abspath(__file__))


def relpath(*args):
    return os.path.normpath(os.path.join(testdir, *args))


class CLexerTestCase(unittest.TestCase):
    """ Test the behavior of the lexer """
    def setUp(self):
        coptions = COptions()
        self.lexer = CLexer(coptions)
        coptions.enable('trigraphs')

    def tokenize(self, src):
        tokens = list(self.lexer.lex(io.StringIO(src), 'a.h'))
        return tokens

    def test_generate_characters(self):
        src = "ab\ndf"
        chars = list(lexer.create_characters(io.StringIO(src), 'a.h'))
        self.assertSequenceEqual([1, 1, 1, 2, 2], [c.loc.row for c in chars])
        self.assertSequenceEqual([1, 2, 3, 1, 2], [c.loc.col for c in chars])

    def test_trigraphs(self):
        src = "??( ??) ??/ ??' ??< ??> ??! ??- ??="
        chars = list(lexer.create_characters(io.StringIO(src), 'a.h'))
        chars = list(lexer.trigraph_filter(chars))
        self.assertSequenceEqual(
            list(r'[ ] \ ^ { } | ~ #'), [c.char for c in chars])
        self.assertSequenceEqual([1] * 17, [c.loc.row for c in chars])
        self.assertSequenceEqual(
            [1, 4, 5, 8, 9, 12, 13, 16, 17, 20, 21, 24, 25, 28, 29, 32, 33],
            [c.loc.col for c in chars])

    def test_trigraph_challenge(self):
        """ Test a nice example for the lexer including some trigraphs """
        src = "Hell??/\no world"
        tokens = self.tokenize(src)
        self.assertSequenceEqual(['Hello', 'world'], [t.val for t in tokens])
        self.assertSequenceEqual([1, 2], [t.loc.row for t in tokens])
        self.assertSequenceEqual([1, 3], [t.loc.col for t in tokens])
        self.assertSequenceEqual(['', ' '], [t.space for t in tokens])
        self.assertSequenceEqual([True, False], [t.first for t in tokens])

    def test_block_comment(self):
        src = "/* bla bla */"
        tokens = self.tokenize(src)
        self.assertEqual([], tokens)

    def test_line_comment(self):
        src = """
        int a; // my nice int
        int
        // ?
        b;
        """
        tokens = [(t.typ, t.val) for t in self.tokenize(src)]
        self.assertSequenceEqual(
            [('BOL', ''), ('ID', 'int'), ('ID', 'a'), (';', ';'),
             ('ID', 'int'), ('ID', 'b'), (';', ';'), ('BOL', '')],
            tokens)

    def test_numbers(self):
        src = "212 215u 0xFeeL 073 032U 30l 30ul"
        tokens = self.tokenize(src)
        self.assertTrue(all(t.typ == 'NUMBER' for t in tokens))
        numbers = list(map(lambda t: cnum(t.val), tokens))
        self.assertSequenceEqual([212, 215, 4078, 59, 26, 30, 30], numbers)

    def test_dotdotdot(self):
        """ Test the lexing of the triple dot """
        src = ". .. ... ....."
        tokens = self.tokenize(src)
        dots = list(map(lambda t: t.typ, tokens))
        self.assertSequenceEqual(['.', '.', '.', '...', '...', '.', '.'], dots)

    def test_character_literals(self):
        """ Test various character literals """
        src = r"'a' '\n' L'\0' '\\' '\a' '\b' '\f' '\r' '\t' '\v' '\11' '\xee'"
        expected_chars = [
            "'a'", r"'\n'", r"L'\0'", r"'\\'", r"'\a'", r"'\b'",
            r"'\f'", r"'\r'", r"'\t'", r"'\v'", r"'\11'", r"'\xee'"]
        tokens = self.tokenize(src)
        self.assertTrue(all(t.typ == 'CHAR' for t in tokens))
        chars = list(map(lambda t: t.val, tokens))
        self.assertSequenceEqual(expected_chars, chars)

    def test_token_spacing(self):
        src = "1239hello"
        # TODO: should this raise an error?
        tokens = self.tokenize(src)

    def test_lexical_error(self):
        src = "'asfdfd'"
        # TODO: should this raise an error?
        with self.assertRaises(CompilerError) as cm:
            tokens = self.tokenize(src)
        self.assertEqual("Expected '", cm.exception.msg)


def gen_tokens(tokens):
    """ Helper function which creates a token iterator """
    col = 1
    for typ, val in tokens:
        loc = lexer.SourceLocation('test.c', 1, col, 1)
        yield lexer.CToken(typ, val, '', False, loc)
        col += 1


class CParserTestCase(unittest.TestCase):
    """ Test the C parser """
    def setUp(self):
        self.parser = CParser(CContext(COptions(), None))

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
        self.assertEqual(0, len(cu.declarations))

    def test_global_int(self):
        """ Test the parsing of a global integer """
        tokens = [('int', 'int'), ('ID', 'A'), (';', ';')]
        cu = self.parse(tokens)
        self.assertEqual(1, len(cu.declarations))
        decl = cu.declarations[0]
        self.assertEqual('A', decl.name)

    def test_function(self):
        """ Test the parsing of a function """
        tokens = [
            ('int', 'int'), ('ID', 'add'), ('(', '('), ('int', 'int'),
            ('ID', 'x'), (',', ','), ('int', 'int'), ('ID', 'y'), (')', ')'),
            ('{', '{'), ('return', 'return'), ('ID', 'x'), ('+', '+'),
            ('ID', 'y'), (';', ';'), ('}', '}')]
        cu = self.parse(tokens)
        self.assertEqual(1, len(cu.declarations))
        decl = cu.declarations[0]
        self.assertIsInstance(decl.typ, nodes.FunctionType)
        self.assertIsInstance(decl.typ.return_type, nodes.BareType)
        stmt = decl.body.statements[0]
        self.assertIsInstance(stmt, nodes.Return)
        self.assertIsInstance(stmt.value, nodes.Binop)
        self.assertEqual('+', stmt.value.op)

    def test_pointer_declaration(self):
        """ Test the proper parsing of a pointer to an integer """
        self.given_source('int *a;')
        declaration = self.parser.parse_declaration()
        # TODO: return a single declaration here?
        declaration = declaration[0]
        self.assertEqual('a', declaration.name)
        self.assertIsInstance(declaration.typ, nodes.PointerType)
        self.assertIsInstance(declaration.typ.pointed_type, nodes.BareType)

    def test_cdecl_example1(self):
        """ Test the proper parsing of 'int (*(*foo)(void))[3]'.

        Example taken from cdecl.org.
        """
        src = 'int (*(*foo)(void))[3];'
        self.given_source(src)
        declaration = self.parser.parse_declaration()
        # TODO: return a single declaration here?
        declaration = declaration[0]
        self.assertEqual('foo', declaration.name)
        self.assertIsInstance(declaration.typ, nodes.PointerType)
        self.assertIsInstance(declaration.typ.pointed_type, nodes.FunctionType)
        function_type = declaration.typ.pointed_type
        self.assertEqual(None, function_type.arguments[0].name)
        self.assertEqual('void', function_type.arguments[0].typ.type_id)
        self.assertEqual('void', function_type.arguments[0].typ.type_id)

    def test_function_returning_pointer(self):
        """ Test the proper parsing of a pointer to a function """
        self.given_source('int *a(int x);')
        declaration = self.parser.parse_declaration()
        # TODO: return a single declaration here?
        declaration = declaration[0]
        self.assertEqual('a', declaration.name)
        self.assertIsInstance(declaration.typ, nodes.FunctionType)
        function_type = declaration.typ
        self.assertEqual('x', function_type.arguments[0].name)
        self.assertIsInstance(function_type.return_type, nodes.PointerType)

    def test_function_pointer(self):
        """ Test the proper parsing of a pointer to a function """
        self.given_source('int (*a)(int x);')
        declaration = self.parser.parse_declaration()
        # TODO: return a single declaration here?
        declaration = declaration[0]
        self.assertEqual('a', declaration.name)
        self.assertIsInstance(declaration.typ, nodes.PointerType)
        self.assertIsInstance(declaration.typ.pointed_type, nodes.FunctionType)
        self.assertEqual('x', declaration.typ.pointed_type.arguments[0].name)

    def test_array_pointer(self):
        """ Test the proper parsing of a pointer to an array """
        self.given_source('int (*a)[3];')
        declaration = self.parser.parse_declaration()
        # TODO: return a single declaration here?
        declaration = declaration[0]
        self.assertEqual('a', declaration.name)
        self.assertIsInstance(declaration.typ, nodes.PointerType)
        self.assertIsInstance(declaration.typ.pointed_type, nodes.ArrayType)
        self.assertEqual('3', declaration.typ.pointed_type.size.value)

    def test_struct_declaration(self):
        """ Test struct declaration parsing """
        self.given_source('struct {int g; } a;')
        declaration = self.parser.parse_declaration()
        # TODO: return a single declaration here?
        declaration = declaration[0]
        self.assertEqual('a', declaration.name)
        self.assertIsInstance(declaration.typ, nodes.StructType)

    def test_union_declaration(self):
        """ Test union declaration parsing """
        self.given_source('union {int g; } a;')
        declaration = self.parser.parse_declaration()
        # TODO: return a single declaration here?
        declaration = declaration[0]
        self.assertEqual('a', declaration.name)
        self.assertIsInstance(declaration.typ, nodes.UnionType)

    def test_expression_precedence(self):
        self.given_source('*l==*r && *l')
        expr = self.parser.parse_expression()
        self.assertIsInstance(expr, nodes.Binop)
        self.assertEqual('&&', expr.op)


class CFrontendTestCase(unittest.TestCase):
    """ Test if various C-snippets build correctly """
    def setUp(self):
        self.builder = CBuilder(ExampleArch(), COptions())

    def do(self, src):
        f = io.StringIO(src)
        try:
            ir_module = self.builder.build(f, None)
        except CompilerError as compiler_error:
            lines = src.split('\n')
            compiler_error.render(lines)
            raise
        assert isinstance(ir_module, ir.Module)
        Verifier().verify(ir_module)

    def test_1(self):
        src = """
        int a;
        void main(int b) {
         a = 10 + b;
        }
        """
        self.do(src)

    def test_2(self):
        src = """
        static int c, d, e;
        static float x;
        char f, g;
        int main() {
          int d;
          d = 20 + c * 10 + c >> 2 - 123;
          return d;
        }
        """
        self.do(src)

    def test_control_structures(self):
        src = """
        int main() {
          int d,i,c;
          c = 2;
          d = 20 + c * 10 + c >> 2 - 123;
          if (d < 10)
          {
            while (d < 20)
            {
              d = d + c * 4;
            }
          }

          if (d > 20)
          {
            do {
              d += c;
            } while (d < 100);
          }
          else
          {
            for (i=i;i<10;i++)
            {

            }
          }
          return d;
        }
        """
        self.do(src)

    def test_4(self):
        """ Test expressions """
        src = """
        int main(int, int c) {
          int d;
          d = 20 + c * 10 + c >> 2 - 123;
          return d;
        }
        """
        self.do(src)

    def test_5(self):
        src = """
        static int G;
        void initialize(int g)
        {
          G = g;
        }
        int main(int, int c) {
          int d = 2;
          initialize(d);
          return d;
        }
        """
        self.do(src)

    def test_type_modifiers(self):
        """ Test the various constructs of type names """
        src = """
        void main() {
        int n;
        n = sizeof(int);
        int *a[3];
        n = sizeof(int *[3]);
        int (*p)[3];
        n = sizeof(int (*)[3]);
        n = sizeof(int *(void));
        }
        int *f(void);
        """
        self.do(src)

    def test_struct(self):
        """ Test structure usage """
        src = """
        typedef struct {int quot, rem; } div_t;
        struct z { int foo; };
        struct s;
        struct s* p;
        struct s {
         struct s *next;
         int b:2+5, c:9, d;
         struct z Z;
        };
        void main() {
         volatile div_t x, *y;
         x.rem = 2;
         y = &x;
         y->quot = x.rem;
         struct s S;
         S.next->next->b = 1;
        }
        """
        self.do(src)

    def test_size_outside_struct(self):
        """ Assert error when using bitsize indicator outside struct """
        src = """
         int b:2+5, c:9, d;
        """
        with self.assertRaises(CompilerError) as cm:
            self.do(src)
        # self.assertEqual('Error', cm.exception.msg)

    def test_wrong_tag_kind(self):
        """ Assert error when using wrong tag kind """
        src = """
        union S { int x;};
        int B = sizeof(struct S);
        """
        with self.assertRaises(CompilerError) as cm:
            self.do(src)
        # self.assertEqual('Error', cm.exception.msg)

    def test_enum(self):
        """ Test enum usage """
        src = """
        void main() {
         enum E { A, B, C };
         enum E e = A;
         e = B;
         e = 2;
        }
        """
        self.do(src)

    def test_sizeof(self):
        """ Test sizeof usage """
        src = """
        void main() {
         int x, *y;
         union U;
         union U u;
         union U { int x; };
         x = sizeof(float*);
         x = sizeof *y;
         x = sizeof(*y);
         x = sizeof(union U);
        }
        """
        self.do(src)


class CastXmlTestCase(unittest.TestCase):
    """ Try out cast xml parsing. """
    def test_test8(self):
        reader = CastXmlReader()
        cu = reader.process(relpath('data', 'c', 'test8.xml'))


if __name__ == '__main__':
    unittest.main()

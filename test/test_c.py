import unittest
from unittest import mock
import io
import os
from ppci.common import CompilerError
from ppci.lang.c import CBuilder, CLexer, lexer, CParser, CSemantics, nodes
from ppci.lang.c import CContext, CSynthesizer
from ppci.lang.c.preprocessor import CTokenPrinter, prepare_for_parsing
from ppci.lang.c.options import COptions
from ppci.lang.c.castxml import CastXmlReader
from ppci.lang.c.utils import cnum, replace_escape_codes
from ppci.arch.example import ExampleArch
from ppci import ir
from ppci.irutils import Verifier
from ppci.binutils.debuginfo import DebugDb


testdir = os.path.dirname(os.path.abspath(__file__))


def relpath(*args):
    return os.path.normpath(os.path.join(testdir, *args))


class CUtilitiesTestCase(unittest.TestCase):
    def test_escape_strings(self):
        """ Test string escape codes """
        src = r'\' \" \? \\ \a \b \f \n \r \t \v \0 \001'
        expected = '\' " ? \\ \a \b \f \n \r \t \v \0 \1'
        result = replace_escape_codes(src)
        self.assertEqual(expected, result)

    def test_escape_unicode(self):
        """ Test string escape unicodes """
        src = r'H \xfe \u1234 \U00010123'
        expected = 'H \xfe \u1234 \U00010123'
        result = replace_escape_codes(src)
        self.assertEqual(expected, result)


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
        tokens = [(t.typ, t.val) for t in self.tokenize(src)]
        self.assertEqual([('BOL', '')], tokens)

    def test_block_comments_and_values(self):
        src = "1/* bla bla */0/*w00t*/"
        tokens = [(t.typ, t.val) for t in self.tokenize(src)]
        self.assertEqual([('NUMBER', '1'), ('NUMBER', '0')], tokens)

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
        numbers = list(map(lambda t: cnum(t.val)[0], tokens))
        self.assertSequenceEqual([212, 215, 4078, 59, 26, 30, 30], numbers)

    def test_assignment_operators(self):
        operators = [
            '+=', '-=', '*=', '/=', '%=', '|=', '<<=', '>>=',
            '&=', '^=', '~=']
        src = " ".join(operators)
        tokens = self.tokenize(src)
        lexed_values = [t.val for t in tokens]
        self.assertSequenceEqual(operators, lexed_values)

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
        context = CContext(COptions(), ExampleArch().info)
        self.semantics = mock.Mock(spec=CSemantics, name='semantics')
        self.parser = CParser(context, self.semantics)

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
        self.assertEquals(5, self.semantics.on_variable_access.call_count)
        self.assertEquals(2, self.semantics.on_ternop.call_count)

    def test_ternary_expression_precedence_case2(self):
        self.given_source('a ? b : c ? d : e')
        expr = self.parser.parse_expression()
        self.assertEquals(5, self.semantics.on_variable_access.call_count)
        self.assertEquals(2, self.semantics.on_ternop.call_count)


class CFrontendTestCase(unittest.TestCase):
    """ Test if various C-snippets build correctly """
    def setUp(self):
        self.builder = CBuilder(ExampleArch(), COptions())

    def do(self, src):
        f = io.StringIO(src)
        try:
            ir_module = self.builder.build(f, None, DebugDb())
        except CompilerError as compiler_error:
            lines = src.split('\n')
            compiler_error.render(lines)
            raise
        assert isinstance(ir_module, ir.Module)
        Verifier().verify(ir_module)

    def expect_errors(self, src, errors):
        with self.assertRaises(CompilerError) as cm:
            self.do(src)
        for row, message in errors:
            self.assertEqual(row, cm.exception.loc.row)
            self.assertRegex(cm.exception.msg, message)

    def test_hello_world(self):
        src = r"""
        void printf(char*, ...);
        void main(int b) {
          printf("Hello \x81 world %i\n", 42);
        }
        """
        self.do(src)

    def test_adjecent_strings(self):
        src = r"""
        void printf(char*);
        void main(int b) {
          printf("Hello" "world\n");
          static unsigned char msg[]= "Woooot\n";
          printf(msg);
        }
        """
        self.do(src)

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
            for (i=i;i<10;i++) { }
            for (i=0;;) { }
            for (;;) { }
          }
          return d;
        }
        """
        self.do(src)

    def test_conditionals(self):
        src = """
        int main() {
          int d, i, c;
          c = (( (d < 10) || (i != c) ) | 22) != 0;
          return c;
        }
        """
        self.do(src)

    def test_expressions(self):
        """ Test various expression constructions """
        src = """
        void main() {
          int a,b,c,d;
          c = 2;
          d = a + b - c / a * b;
          d = !a;
          d = a ? b : c + 2;
        }
        """
        self.do(src)

    def test_4(self):
        """ Test expressions """
        src = """
        int main(int, int c) {
          int stack[2];
          struct { int ptr;} *s;
          int d;
          d = 20 + c * 10 + c >> 2 - 123;
          d = stack[--s->ptr];
          --d;
          d--;
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
        volatile const int * volatile vc;
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
         int *g;
        };
        struct s AllocS;
        void main() {
         volatile div_t x, *y;
         x.rem = 2;
         y = &x;
         y->quot = x.rem = sizeof *AllocS.g;
         struct s S;
         S.next->next->b = 1;
        }
        """
        self.do(src)

    def test_union(self):
        """ Test union usage """
        src = """
        union z { int foo; struct { int b, a, r; } bar;};
        union z myZ[2] = {1, 2, 3};
        void main() {
          union z localZ[2] = {1, 2, 3};
        }
        """
        self.do(src)

    def test_array(self):
        """ Test array types """
        src = """
        int a[10];
        int b[] = {1, 2};
        int bbb[] = {1, 2,}; // Trailing comma
        void main() {
         int c[sizeof(long int)/sizeof(char)];
         unsigned long long d[] = {1ULL, 2ULL};
         a[2] = b[10] + c[2] + d[1];
         int* p = a + 2;
         int A[][3] = {1,2,3,4,5,6,7,8,9};
        }
        """
        self.do(src)

    def test_array_index_pointer(self):
        """ Test array indexing of a pointer type """
        src = """
        void main() {
         int* a, b;
         b = a[100];
        }
        """
        self.do(src)

    def test_size_outside_struct(self):
        """ Assert error when using bitsize indicator outside struct """
        src = """
         int b:2+5, c:9, d;
        """
        self.expect_errors(src, [(2, 'Expected ";"')])

    def test_wrong_tag_kind(self):
        """ Assert error when using wrong tag kind """
        src = """
        union S { int x;};
        int B = sizeof(struct S);
        """
        self.expect_errors(src, [(3, 'Wrong tag kind')])

    def test_enum(self):
        """ Test enum usage """
        src = """
        void main() {
         enum E { A, B, C=A+10 };
         enum E e = A;
         e = B;
         e = 2;
        }
        """
        self.do(src)

    def test_literal_data(self):
        """ Test various formats of literal data """
        src = """
        void main() {
         int i;
         char *s, c;
         i = 10l;
         s = "Hello!" "World!";
         c = ' ';
        }
        """
        self.do(src)

    def test_assignment_operators(self):
        """ Test assignment operators """
        src = """
        void main() {
         int a, b, c;
         a += b - c;
         a -= b - c;
         a /= b - c;
         a %= b - c;
         a |= b - c;
         a &= b - c;
        }
        """
        self.do(src)

    def test_sizeof(self):
        """ Test sizeof usage """
        src = """
        void main() {
         int x, *y;
         union U;
         union U { int x; };
         union U u;
         x = sizeof(float*);
         x = sizeof *y;
         x = sizeof(*y);
         x = sizeof(union U);
         int w = sizeof w;  // Sizeof works on the expression before the '='
        }
        """
        self.do(src)

    def test_goto(self):
        """ Test goto statements """
        src = """
        void main() {
          goto part2;
          part2: goto part2;
          switch(0) {
           case 34: break;
           default: break;
          }
        }
        """
        self.do(src)

    def test_continue(self):
        """ Test continue statement """
        src = """
        void main() {
          while (1) {
            continue;
          }
        }
        """
        self.do(src)

    def test_break(self):
        """ Test break statement """
        src = """
        void main() {
          while (1) {
            break;
          }
        }
        """
        self.do(src)

    def test_switch(self):
        """ Test switch statement """
        src = """
        void main() {
          int a;
          short b = 23L;
          switch (b) {
            case 34:
              a -= 5;
              break;
            case 342LL:
              break;
            default:
              a += 2;
              break;
          }
        }
        """
        self.do(src)

    def test_loose_case(self):
        """ Test loose case statement """
        src = """
        void main() {
          case 34: break;
        }
        """
        self.expect_errors(src, [(3, 'Case statement outside')])

    def test_loose_default(self):
        """ Test loose default statement """
        src = """
        void main() {
          default: break;
        }
        """
        self.expect_errors(src, [(3, 'Default statement outside')])

    def test_void_function(self):
        """ Test calling of a void function """
        src = """
        void main(void) {
          main();
        }
        """
        self.do(src)

    def test_function_arguments(self):
        """ Test calling of functions """
        src = """
        void add(int a, int b, int c);
        void main() {
          add((int)22, 2, 3);
        }
        """
        self.do(src)

    def test_forward_declaration(self):
        """ Test forward declarations """
        src = """
        extern char a;
        char a = 2;
        """
        self.do(src)

    def test_softfloat_bug(self):
        """ Bug encountered in softfloat library """
        src = """
        #define INLINE
        typedef short int16;
        typedef unsigned int bits32;
        typedef char int8;

        INLINE void
         shift64ExtraRightJamming(
             bits32 a0,
             bits32 a1,
             bits32 a2,
             int16 count,
             bits32 *z0Ptr,
             bits32 *z1Ptr,
             bits32 *z2Ptr
         )
        {
            bits32 z0, z1, z2;
            int8 negCount = ( - count ) & 31;

            if ( count == 0 ) {
                z2 = a2;
                z1 = a1;
                z0 = a0;
            }
            else {
                if ( count < 32 ) {
                    z2 = a1<<negCount;
                    z1 = ( a0<<negCount ) | ( a1>>count );
                    z0 = a0>>count;
                }
                else {
                    if ( count == 32 ) {
                        z2 = a1;
                        z1 = a0;
                    }
                    else {
                        a2 |= a1;
                        if ( count < 64 ) {
                            z2 = a0<<negCount;
                            z1 = a0>>( count & 31 );
                        }
                        else {
                            z2 = ( count == 64 ) ? a0 : ( a0 != 0 );
                            z1 = 0;
                        }
                    }
                    z0 = 0;
                }
                z2 |= ( a2 != 0 );
            }
            *z2Ptr = z2;
            *z1Ptr = z1;
            *z0Ptr = z0;

        }
        """
        self.do(src)


class CastXmlTestCase(unittest.TestCase):
    """ Try out cast xml parsing. """
    def test_test8(self):
        reader = CastXmlReader()
        cu = reader.process(relpath('data', 'c', 'test8.xml'))


class CSynthesizerTestCase(unittest.TestCase):
    @unittest.skip('todo')
    def test_hello(self):
        """ Convert C to Ir, and then this IR to C """
        src = r"""
        void printf(char*);
        void main(int b) {
          printf("Hello" "world\n");
        }
        """
        builder = CBuilder(ExampleArch(), COptions())
        f = io.StringIO(src)
        try:
            ir_module = builder.build(f, None)
        except CompilerError as compiler_error:
            lines = src.split('\n')
            compiler_error.render(lines)
            raise
        assert isinstance(ir_module, ir.Module)
        Verifier().verify(ir_module)
        synthesizer = CSynthesizer()
        synthesizer.syn_module(ir_module)


if __name__ == '__main__':
    unittest.main()

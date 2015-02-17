import unittest
import logging
import io
from ppci.c3 import Builder, Lexer
from ppci.target import SimpleTarget
from ppci import DiagnosticsManager, CompilerError
from ppci.irutils import Verifier


class LexerTestCase(unittest.TestCase):
    """ Test lexer """
    def setUp(self):
        diag = DiagnosticsManager()
        self.l = Lexer(diag)

    def testUnexpectedCharacter(self):
        snippet = io.StringIO(""" var s \u6c34 """)
        with self.assertRaises(CompilerError):
            list(self.l.lex(snippet))

    def check(self, snippet, toks):
        """ Convenience function """
        toks2 = list(tok.typ for tok in self.l.lex(io.StringIO(snippet)))
        self.assertSequenceEqual(toks, toks2)

    def test_block_comment(self):
        """ See if block comment works """
        snippet = """
          /* Demo */
          var int x = 0;
        """
        toks = ['var', 'ID', 'ID', '=', 'NUMBER', ';', 'EOF']
        self.check(snippet, toks)

    def test_block_comment_multi_line(self):
        """ Test block comment over multiple lines """
        snippet = """
          /* Demo
          bla1
          bla2
          */
          var int x = 0;
        """
        toks = ['var', 'ID', 'ID', '=', 'NUMBER', ';', 'EOF']
        self.check(snippet, toks)


class BuildTestCaseBase(unittest.TestCase):
    """ Test if various snippets build correctly """
    def setUp(self):
        self.diag = DiagnosticsManager()
        self.builder = Builder(self.diag, SimpleTarget())
        self.diag.clear()
        # Add a null logging handler to disable warning log messages:
        null_handler = logging.NullHandler()
        logging.getLogger().addHandler(null_handler)

    def make_file_list(self, snippet):
        """ Try to make a list with opened files """
        if type(snippet) is list:
            files = []
            for src in snippet:
                if type(src) is str:
                    files.append(io.StringIO(src))
                else:
                    files.append(src)
            return files
        else:
            return [io.StringIO(snippet)]

    def build(self, snippet):
        """ Try to build a snippet """
        try:
            return list(self.builder.build(self.make_file_list(snippet)))
        except CompilerError:
            pass

    def expect_errors(self, snippet, rows):
        """ Helper to test for expected errors on rows """
        self.build(snippet)
        actual_errors = [err.row for err in self.diag.diags]
        if rows != actual_errors:
            self.diag.printErrors()
        self.assertSequenceEqual(rows, actual_errors)

    def expect_ok(self, snippet):
        """ Expect a snippet to be OK """
        ircode = self.build(snippet)
        if len(self.diag.diags) > 0:
            self.diag.printErrors()
        self.assertTrue(ircode)
        verifier = Verifier()
        for mod in ircode:
            verifier.verify(mod)
        self.assertEqual(0, len(self.diag.diags))


class ModuleTestCase(BuildTestCaseBase):
    """ Module related tests """
    def test_empty(self):
        """ Check what happens when an empty file is supplied """
        snippet = """
        module A
        """
        self.expect_errors(snippet, [3])

    def test_empty2(self):
        """ Check what an empty source file does """
        snippet = ""
        self.expect_errors(snippet, [1])

    def test_module(self):
        """ Test module idea """
        src1 = """module mod1;
        type int A;
        """
        src2 = """module mod2;
        import mod1;
        var mod1.A b;
        """
        self.expect_ok([src1, src2])

    def test_module_with_function(self):
        """ Test if a function can have the same name as the module. """
        src1 = """module mod1;
        function void mod1()
        {
        }
        """
        self.expect_ok(src1)

    def test_module_distributed(self):
        """ Check if a single module can be build from two source files """
        src1 = """module p1;
        type int A;
        """
        src2 = """module p1;
        var A b;
        """
        self.expect_ok([src1, src2])

    def test_package_mutual(self):
        """ Check if two packages can import eachother """
        src1 = """module mod1;
        import mod2;
        type int A;
        var mod2.B b;
        """
        src2 = """module mod2;
        import mod1;
        type int B;
        var mod1.A a;
        """
        self.expect_ok([src1, src2])

    def test_module_does_not_exist(self):
        """ Check if importing an undefined module raises an error """
        src1 = """module p1;
        import p23;
        """
        self.expect_errors(src1, [0])

    def test_module_references(self):
        """ Check if membership variables work as expected """
        src1 = """
        module m1;
        import m2;
        var int A;
        function void t()
        {
            m2.A = 2;
            m2.t();
        }
        """
        src2 = """
        module m2;
        import m1;
        var int A;
        function void t()
        {
            m1.A = 1;
            m1.t();
            m1.m2.m1.m2.A = 3;
        }
        """
        self.expect_ok([src1, src2])


class ConstantTestCase(BuildTestCaseBase):
    """ Testcase for constants """
    def test_constant(self):
        """ Test good usage of constant """
        snip = """module C;
        const int a = 2;
        function int reta()
        {
            var int b;
            b = a + 2;
            return addone(a);
        }

        function int addone(int x)
        {
            return x + 1;
        }
        """
        self.expect_ok(snip)

    def test_constant_mutual(self):
        """ A circular dependency of constants must be fatal """
        snip = """module C;
        const int a = c + 1;
        const int b = a + 1;
        const int c = b + 1;
        function void f()
        {
           return a;
        }
        """
        self.expect_errors(snip, [2])


class FunctionTestCase(BuildTestCaseBase):
    """ Test function syntax """
    def test_function_args(self):
        """ Test function arguments """
        snippet = """
         module testargs;
         function void t1(int a, double b)
         {
            t1(2, 2);
            t1(2);
            t1(1, 1.2);
         }

         function void t2(struct {int a; int b;} x)
         {
         }

         function int t3()
         {
            t3();
         }
        """
        self.expect_errors(snippet, [5, 6, 10, 16])

    def test_return(self):
        """ Test return of void """
        snippet = """
         module testreturn;
         function void t()
         {
            return;
         }
        """
        self.expect_ok(snippet)

    def test_return2(self):
        """ Test the return of a value """
        snippet = """
         module testreturn;
         function int t()
         {
            return 2;
         }
        """
        self.expect_ok(snippet)


class ConditionTestCase(BuildTestCaseBase):
    def test_and_condition(self):
        """ Test logical 'and' """
        snippet = """
        module tst;
        function void t()
        {
         if (4 > 3 and 1 < 10)
         {
         }
        }
        """
        self.expect_ok(snippet)

    def test_or_condition(self):
        snippet = """
        module tst;
        function void t()
        {
         if (3 > 4 or 3 < 10)
         {
         }
        }
        """
        self.expect_ok(snippet)

    def test_non_bool_condition(self):
        snippet = """
        module tst;
        function void t()
        {
         if (3+3)
         {
         }
        }
        """
        self.expect_errors(snippet, [5])

    def test_expression_as_condition(self):
        """ Test if an expression as a condition works """
        snippet = """
        module tst;
        function bool yes()
        {
            return true;
        }

        function void t()
        {
         if (yes())
         {
         }
         while(yes() or 1 == 2)
         {
         }
         if (false == yes())
         {
         }
        }
        """
        self.expect_ok(snippet)


class ExpressionTestCase(BuildTestCaseBase):
    """ Test various expressions """
    def test_expressions(self):
        snippet = """
         module test;
         function void t(int a, double b)
         {
            var int a2;
            var bool c;

            a2 = b * a;
            c = a;
         }
        """
        self.expect_errors(snippet, [8, 9])

    def test_expression1(self):
        """ Test some other expressions """
        snippet = """
         module testexpr1;
         function void t()
         {
            var int a, b, c;
            a = 1;
            b = a * 2 + a * a;
            c = b * a - 3;
         }
        """
        self.expect_ok(snippet)

    def test_unary_minus(self):
        """ Check if a = -1 works """
        snippet = """
         module testunaryminus;
         function void t()
         {
            var int a, b, c;
            a = -11;
            b = -a * -2 + - a * a;
            c = b * a - -3;
         }
        """
        self.expect_ok(snippet)

    def test_redefine(self):
        """ Check if redefining a symbol results in error """
        snippet = """
        module test;
        var int a;
        var int b;
        var int a;
        """
        self.expect_errors(snippet, [5])


class StatementTestCase(BuildTestCaseBase):
    """ Testcase for statements """
    def test_assignments(self):
        """ Check if normal assignments and |= &= assignments work """
        snippet = """
        module test;
        function void tst()
        {
         var int i;
         i = 2;
         i |= 0xf00;
         i &= 0xf;
         i += 22;
         i -= 15;
         i *= 33;
        }
        """
        self.expect_ok(snippet)

    def test_while(self):
        snippet = """
        module tstwhile;
        function void t()
        {
         var int i;
         i = 0;
         while (i < 1054)
         {
            i = i + 3;
         }
        }
        """
        self.expect_ok(snippet)

    def test_while2(self):
        snippet = """
        module tstwhile;
        function void t()
        {
         while(true)
         {
         }

         while(false)
         {
         }
        }
        """
        self.expect_ok(snippet)

    def test_if(self):
        snippet = """
        module tstIFF;
        function void t(int b)
        {
         var int a;
         a = 2;
         if (a > b)
         {
            if (a > 1337)
            {
               b = 2;
            }
         }
         else
         {
            b = 1;
         }

         return b;
        }
        """
        self.expect_ok(snippet)

    def test_local_variable(self):
        snippet = """
         module testlocalvar;
         function void t()
         {
            var int a, b;
            a = 2;
            b = a + 2;
         }
        """
        self.expect_ok(snippet)

    def test_array(self):
        snippet = """
         module testarray;
         function void t()
         {
            var int[100] x;
            var int a, b;
            a = 2;
            b = x[a*2+9 - a] * x[22+x[12]];
            x[1] = x[2];
         }
        """
        self.expect_ok(snippet)

    def test_array_fail(self):
        snippet = """
         module testarray;
         function void t()
         {
            var bool c;
            c = false;
            var int[100] x;
            x[1] = x[c];
         }
        """
        self.expect_errors(snippet, [8])

    def test_array_fail2(self):
        """ Check that non-array cannot be indexed """
        snippet = """
         module testarray;
         function void t()
         {
            var int c;
            var int x;
            c = x[2];
         }
        """
        self.expect_errors(snippet, [7])

    def test_array_fail3(self):
        snippet = """
         module testarray;
         function void t()
         {
            var int[20] c;
         }
        """
        self.expect_ok(snippet)

    def test_struct_call(self):
        """ A struct type cannot be called """
        snippet = """
         module teststruct1;
         function void t()
         {
            var struct {int x, y;} a;
            a.x(9);
         }
        """
        self.expect_errors(snippet, [6])

    def test_string(self):
        """ Test string literals """
        snippet = """
         module teststring;
         function void t()
         {
            var string a;
            a = "Hello world";
            print(a);
            print("Moi");
         }

         function void print(string a)
         {
         }
        """
        self.expect_ok(snippet)


class TypeTestCase(BuildTestCaseBase):
    """ Test type related syntax """
    def test_typedef(self):
        """ Check if a type can be defined """
        snippet = """
         module testtypedef;
         type int my_int;
         function void t()
         {
            var my_int a;
            var int b;
            a = 2;
            b = a + 2;
         }
        """
        self.expect_ok(snippet)

    def test_sizeof1(self):
        snippet = """
         module testsizeof;

         function void t()
         {
            var int a;
            a = sizeof(int*);
         }
        """
        self.expect_ok(snippet)

    def test_sizeof2(self):
        """ Sizeof must not be assignable """
        snippet = """
         module testsizeof2;

         function void t()
         {
            sizeof(int*) = 2;
         }
        """
        self.expect_errors(snippet, [6])

    def test_wrong_var_use(self):
        snippet = """
         module testsizeof;

         function void t()
         {
            var int a;
            a = 1;
         }
        """
        self.expect_ok(snippet)

    def test_unknown_type(self):
        """ Check if an unknown type is detected """
        snippet = """module testlocalvar;
         function void t()
         {
            var int2 a;
         }
        """
        self.expect_errors(snippet, [4])

    def test_struct1(self):
        """ Test struct syntax """
        snippet = """
         module teststruct1;
         function void t()
         {
            var struct {int x, y;} a;
            a.x = 2;
            a.y = a.x + 2;
         }
        """
        self.expect_ok(snippet)

    def test_struct2(self):
        """ Select struct member from non struct type """
        snippet = """
         module teststruct1;
         function void t()
         {
            var int a;
            a.z = 2;
         }
        """
        self.expect_errors(snippet, [6])

    def test_pointer_type1(self):
        """ Check if pointers work """
        snippet = """
         module testpointer1;
         var int* pa;
         function void t()
         {
            var int a;
            pa = &a;
            *pa = 22;
            a = *pa + *pa * 8;
         }
        """
        self.expect_ok(snippet)

    def test_pointer_type(self):
        """ Check if pointers work """
        snippet = """
         module testpointer;
         var int* pa, pb;
         function void t(int a, double b)
         {
            var int a2;
            a2 = a; // parameters cannot be escaped for now..
            pa = &a2;
            pb = pa;
            *pa = 22;
         }
        """
        self.expect_ok(snippet)

    def test_pointer_coercion(self):
        """ Check coercion """
        snippet = """
         module testcoerce;
         var int* pa;
         function void t()
         {
            pa = 22;
            pa = pa - 23;
         }
        """
        self.expect_ok(snippet)

    def test_pointer_type_incorrect(self):
        """ Test invalid pointer assignments """
        snippet = """
         module testpointerincorrect;
         var int* pa;
         function void t(int a, double b)
         {
            pa = 2; // this is OK due to coercion
            pa = &a;
            pa = &2; // No valid lvalue
            &a = pa; // No valid lvalue
            **pa = 22; // Cannot deref int
         }
        """
        self.expect_errors(snippet, [8, 9, 10])

    def test_pointer_to_basetype(self):
        """ Test pointer """
        snippet = """
         module testptr_ir;
         function void t()
         {
            var int* a;
            a = cast<int*>(40);
            *a = 2;
            var byte* b;
            b = cast<byte*>(40);
            *b = cast<byte>(2);
         }
        """
        self.expect_ok(snippet)

    def test_pointer_type_ir2(self):
        """ Test pointer to struct """
        snippet = """
         module testptr_ir;
         type struct {int x,y;}* gpio;
         function void t()
         {
            var gpio a;
            a = cast<gpio>(40);
            a->x = 2;
            a->y = a->x - 14;
         }
        """
        self.expect_ok(snippet)

    def test_pointer_arithmatic(self):
        """ Check if pointer arithmatic works """
        snippet = """
         module testpointerarithmatic;
         function void t()
         {
            var int* pa;
            *(pa+2) = 2;
         }
        """
        self.expect_ok(snippet)

    def test_wrong_cast(self):
        """ See if a wrong cast cannot be done """
        snippet = """
         module testptr_ir;
         type struct {int x,y;}* gpio;
         function void t()
         {
            var gpio a;
            *cast<gpio>(*a);
         }
        """
        self.expect_errors(snippet, [7])

    def test_linked_list(self):
        """
            Test if a struct can contain a field with a pointer to itself
        """
        snippet = """
         module testlinkedlist;

         type struct {
            int x;
            list_t* next;
         } list_t;

         function void t()
         {
            var list_t* a;
            a = a->next;
         }
        """
        self.expect_ok(snippet)

    def test_infinite_struct(self):
        """
            Test if a struct can contain a field with itself as type?
            This should not be possible!
        """
        snippet = """
         module testnestedstruct;

         type struct
         {
            int x;
            list_t inner;
         } list_t;

        """
        self.expect_errors(snippet, [0])

    def test_mutual_structs(self):
        """
            Test if two structs can contain each other!
            This should not be possible!
        """
        snippet = """
         module testnestedstruct;

         type struct
         {
            int x;
            B other;
         } A;

         type struct
         {
            int x;
            A other;
         } B;

        """
        self.expect_errors(snippet, [0])

    def test_complex_type(self):
        """ Test if a complex typedef works """
        snippet = """
         module testpointer;
         type int my_int;

         type struct {
          int x, y;
         } point;

         type struct {
           int mem1;
           int memb2;
           point P1;
         } my_struct;

         type my_struct* my_sptr;
         var int* pa;

         function void t(int a, int b, my_sptr x)
         {
            var my_struct *msp;

            var my_struct u, v;
            var point *pt;

            pt = &msp->P1;
            msp = x;
            *pa = 22 + u.mem1 * v.memb2 - u.P1.x;
            x->memb2 = *pa + a * b;

            msp->P1.x = a * x->P1.y;
         }
        """
        self.expect_ok(snippet)


if __name__ == '__main__':
    unittest.main()

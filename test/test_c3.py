import unittest
import logging
import io
from ppci.lang.c3 import C3Builder, Lexer, Parser, AstPrinter, Context
from ppci.arch.example import ExampleArch
from ppci.common import DiagnosticsManager, CompilerError
from ppci.irutils import Verifier


class LexerTestCase(unittest.TestCase):
    """ Test lexer """
    def setUp(self):
        diag = DiagnosticsManager()
        self.l = Lexer(diag)

    def test_unexpected_character(self):
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


class AstPrinterTestCase(unittest.TestCase):
    def test_print(self):
        """ See if the ast can be printed using the visitor pattern """
        snippet = """
        module tstwhile;
        type int A;
        function void t()
        {
          var A i;
          i = 0;
          while (i < 1054)
          {
            i = i + 3;
          }
        }
        """
        diag = DiagnosticsManager()
        lexer = Lexer(diag)
        parser = Parser(diag)
        context = Context(ExampleArch())
        tokens = lexer.lex(io.StringIO(snippet))
        ast = parser.parse_source(tokens, context)
        printer = AstPrinter()
        f = io.StringIO()
        printer.print_ast(ast, f)
        self.assertTrue(f.getvalue())
        str(ast.inner_scope)


class BuildTestCaseBase(unittest.TestCase):
    """ Test if various snippets build correctly """
    def setUp(self):
        self.diag = DiagnosticsManager()
        self.builder = C3Builder(self.diag, ExampleArch())
        self.diag.clear()
        # Add a null logging handler to disable warning log messages:
        null_handler = logging.NullHandler()
        logging.getLogger().addHandler(null_handler)

    def make_file_list(self, snippet):
        """ Try to make a list with opened files """
        if isinstance(snippet, list):
            files = []
            for src in snippet:
                if isinstance(src, str):
                    files.append(io.StringIO(src))
                else:
                    files.append(src)
            return files
        else:
            return [io.StringIO(snippet)]

    def build(self, snippet):
        """ Try to build a snippet and also print it to test the printer """
        srcs = self.make_file_list(snippet)
        context, ir_modules, debug_info = self.builder.build(srcs)
        printer = AstPrinter()
        for mod in context.modules:
            output_file = io.StringIO()
            printer.print_ast(mod, output_file)

        return ir_modules

    def expect_errors(self, snippet, rows):
        """ Helper to test for expected errors on rows """
        with self.assertRaises(CompilerError):
            self.build(snippet)
        actual_errors = [
            err.loc.row if err.loc else 0 for err in self.diag.diags]
        if rows != actual_errors:
            self.diag.print_errors()
        self.assertSequenceEqual(rows, actual_errors)

    def expect_ok(self, snippet):
        """ Expect a snippet to be OK """
        ircode = self.build(snippet)
        if len(self.diag.diags) > 0:
            self.diag.print_errors()
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

    def test_incorrect_top_level(self):
        """ See what an incorrect top level statement does """
        snippet = """module tst;
        foo bar;"""
        self.expect_errors(snippet, [2])

    def test_module(self):
        """ Test module idea """
        src1 = """module mod1;
        public type int A;
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

    def test_module_double_import(self):
        """ Check redefine causes error """
        src1 = """module p1;
        """
        src2 = """module p2;
        import p1;
        import p1;
        """
        self.expect_errors([src1, src2], [0])

    def test_package_mutual(self):
        """ Check if two packages can import eachother """
        src1 = """module mod1;
        import mod2;
        public type int A;
        var mod2.B b;
        """
        src2 = """module mod2;
        import mod1;
        public type int B;
        var mod1.A a;
        """
        self.expect_ok([src1, src2])

    def test_no_access_to_private(self):
        """ Check if private members are protected """
        src1 = """module mod1;
        type int A;
        """
        src2 = """module mod2;
        import mod1;
        var mod1.A a;
        """
        self.expect_errors([src1, src2], [3])

    def test_module_does_not_exist(self):
        """ Check if importing an undefined module raises an error """
        src1 = """module p1;
        import p23;
        """
        self.expect_errors(src1, [0])

    def test_module_as_arithmatic(self):
        """ Using module in arithmatic is an error """
        src1 = """module p1;
        import mod2;
        function void p()
        {
            var int a = mod2 + 2;
        }
        """
        src2 = """module mod2;
        """
        self.expect_errors([src1, src2], [5])

    def test_module_references(self):
        """ Check if membership variables work as expected """
        src1 = """
        module m1;
        import m2;
        var int A;
        public function void t()
        {
            m2.A = 2;
            m2.t();
        }
        """
        src2 = """
        module m2;
        import m1;
        var int A;
        public function void t()
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

    def test_constant_byte(self):
        """ Test good usage of constant """
        snip = """module C;
        const byte a = 2 + 99;
        const int c = a + 13;
        function int reta()
        {
            var int b;
            b = a + 2 + c;
            return b;
        }
        """
        self.expect_ok(snip)

    def test_constant_mutual(self):
        """ A circular dependency of constants must be fatal """
        snip = """module C;
        const int a = c + 1;
        const int b = a + 1;
        const int c = b + 1;
        function int f()
        {
            var int x = a;
           return 0;
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
            return 0;
         }

        """
        self.expect_errors(snippet, [6, 10, 16])

    def test_call_of_non_function(self):
        """ Test if the call to a non-function type raises an error """
        snippet = """
         module testreturn;
         var int x;
         function void t()
         {
            x();
            return;
         }
        """
        self.expect_errors(snippet, [6])

    def test_call_bad_function(self):
        """ Test if the call to struct returning function raises an error """
        snippet = """
         module testreturn;
         var int x;
         function struct {int a;} bad();
         function void t()
         {
            bad();
         }
        """
        self.expect_errors(snippet, [4, 7])

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

    def test_return_value(self):
        """ Test the return of a value """
        snippet = """
         module testreturn;
         function int t()
         {
            return 2;
         }
        """
        self.expect_ok(snippet)

    def test_no_return_from_function(self):
        """ Test that returning nothing in a function is an error """
        snippet = """
         module main;
         function int t3()
         {
            var int a;
            a = 2;
         }
        """
        self.expect_errors(snippet, [3])

    def test_return_void_from_function(self):
        """ Test that returning nothing in a function is an error """
        snippet = """
         module main;
         function int t3()
         {
            return;
         }
        """
        self.expect_errors(snippet, [5])

    def test_return_expr_from_procedure(self):
        """ Test that returning a value from a void function is an error """
        snippet = """
         module main;
         function void t3()
         {
            return 6;
         }
        """
        self.expect_errors(snippet, [5])

    def test_return_complex_type(self):
        """ Test the return of a complex value, this is not allowed """
        snippet = """
         module testreturn;
         function struct {int a;int b;} t()
         {
            var int a = t();
            return 2;
         }
        """
        self.expect_errors(snippet, [3])

    def test_parameter_redefine(self):
        """ Check if a parameter and variable with the same name result in
            error
        """
        snippet = """
         module testreturn;
         function int t(int x)
         {
            var int x;
         }
        """
        self.expect_errors(snippet, [5])

    def test_prototype_function(self):
        """ Check if a prototype function works good """
        snippet = """
         module tst;
         function int t(int x);
        """
        self.expect_ok(snippet)


class ConditionTestCase(BuildTestCaseBase):
    """ Test conditional logic, such as and and or in if and while statements
        and == and >=. Also test boolean assignments
    """
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

    def test_byte_compare(self):
        snippet = """
        module tst;
        function void t()
        {
         var byte a = 2;
         if (a <= 22)
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
         if (3 + 3)
         {
         }
        }
        """
        self.expect_errors(snippet, [5])

    def test_non_bool_expr_condition(self):
        snippet = """
        module tst;
        var int B;
        function void t()
        {
         if (B)
         {
         }
        }
        """
        self.expect_errors(snippet, [6])

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

    def test_unary_plus(self):
        """ Check if a = +1 works """
        snippet = """
         module testunaryplus;
         function void t()
         {
            var int a, b, c;
            a = + 11;
            b = -a * + 2 + - a * a;
            c = b * a - +3;
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

    def test_type_in_expression(self):
        """ Check if arithmatic with types generates errors """
        snippet = """module test;
        var int a;
         function void t()
         {
            var int a = 2 + int;
         }
        """
        self.expect_errors(snippet, [5])

    @unittest.skip('Fix this')
    def test_uninitialized_local(self):
        """ When a variable is not initialized before it is used, an error
            is expected """
        snippet = """
         module test;
         var int b;
         function int start()
         {
            var int x;
            b = x;
            return x;
         }
        """
        # TODO: this error diagnostics must be improved!
        self.expect_errors(snippet, [0])

    @unittest.skip('Fix this')
    def test_array_initialization(self):
        """ Check array initialization """
        snippet = """
        module test;
        var int[5] a = {1,4,4,4,4};
        """
        self.expect_errors(snippet, [5])


class StatementTestCase(BuildTestCaseBase):
    """ Testcase for statements """
    def test_empty_twice(self):
        snippet = """
        module tst;
        function void t()
        {
            ;;;
        }
        """
        self.expect_ok(snippet)

    def test_assignments(self):
        """ Check if normal assignments and |= &= assignments work """
        snippet = """
        module test;
        function void tst()
        {
         var int i = 2;
         i |= 0xf00;
         i &= 0xf;
         i += 22;
         i -= 15;
         i *= 33;
        }
        """
        self.expect_ok(snippet)

    def test_while(self):
        """ Test the while statement """
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

    def test_for(self):
        """ Test the while statement """
        snippet = """
        module tstfor;
        function void t()
        {
         var int i;
         i = 0;
         for (i=0; i < 1054; i=i+1)
         {
         }
        }
        """
        self.expect_ok(snippet)

    def test_if(self):
        snippet = """
        module tstIFF;
        function int t(int b)
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

    def test_switch(self):
        """ Test switch case statement """
        snippet = """
        module tst;
        function int t()
        {
         var int a;
         a = 2;
         switch(a) {
           case 2:
             { return 3; }
           case 4:
             { a = 3 }
           default:
             { return 77; }
         }

         return a;
        }
        """
        self.expect_ok(snippet)

    def test_switch_without_default(self):
        """ Test switch case statement without default case """
        snippet = """
        module tst;
        function int t()
        {
         var int a;
         a = 2;
         switch(a) {
           case 4:
             { a = 3 }
         }

         return a;
        }
        """
        self.expect_errors(snippet, [7])

    def test_switch_invalid_syntax(self):
        """ Test switch case statement with invalid syntax """
        snippet = """
        module tst;
        function int t()
        {
         var int a;
         switch(a) {
           a += 2;
         }

         return a;
        }
        """
        self.expect_errors(snippet, [7])

    def test_switch_on_invalid_type(self):
        """ Test switch case statement on invalid type """
        snippet = """
        module tst;
        function void t()
        {
         var float a;
         switch(a) {
         }
        }
        """
        self.expect_errors(snippet, [6])

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

    def test_expression_statement(self):
        """ Make sure an expression cannot be a statement """
        snippet = """
         module teststruct1;
         function void t()
         {
            2;
         }
        """
        self.expect_errors(snippet, [5])


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
        """ Check basic behavior of sizeof """
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

    def test_enum(self):
        """ Test enum syntax """
        snippet = """
         module testenum;
         function void t()
         {
            var enum a;
         }
        """
        with self.assertRaises(NotImplementedError):
            self.expect_ok(snippet)

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

    def test_nonstruct_member(self):
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

    def test_struct_unequal(self):
        """ Select struct member from non struct type """
        snippet = """
         module teststruct1;
         type struct { int a, b; } T1;
         type struct { int a; } T2;
         function void t()
         {
            var T1* a;
            var T2* b;
            b = a;
         }
        """
        self.expect_ok(snippet)

    def test_nonexisting_struct_member(self):
        """ Select field that is not in struct type """
        snippet = """
         module teststruct1;
         type struct { int a, b; } T1;
         function void t()
         {
            var T1 a;
            a.z = 2;
         }
        """
        self.expect_errors(snippet, [7])

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
         var byte* pb;
         function void t()
         {
            pa = 22;
            pa = pa - 23;
            pa = pb;
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
            *b = 2;
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
            pa = 0;
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

    def test_integer_casting(self):
        snippet = """
         module testptr_ir;
         function void test(string txt)
         {
            var int x;
            x = cast<int>(txt->txt[1]);
         }
        """
        self.expect_ok(snippet)

    def test_float_coerce(self):
        snippet = """
         module test;
         function void test()
         {
            var float x;
            var double y;
            x = 2;
            y = x;
            y = x - 100;
         }
        """
        self.expect_ok(snippet)

    def test_float_literal(self):
        snippet = """
         module test;
         function void test()
         {
            var double y;
            var float z;
            y = 3.1415926;
            z = 2.7;
         }
        """
        self.expect_ok(snippet)

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
            var list_t b;
            a = &b;
            a->next = a;
            a = a->next;
            a = a->next->next->next;
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
            msp = &u;
            var point *pt;

            pt = &msp->P1;
            msp = x;
            *pa = 22 + u.mem1 * v.memb2 - u.P1.x;
            x->memb2 = *pa + a * b;

            msp->P1.x = a * x->P1.y;
         }
        """
        self.expect_ok(snippet)

    def test_complex_type_assignment(self):
        """ Complex type cannot be assigned """
        snippet = """
         module test;

         type struct {
          int x, y;
         } point;

         function void t()
         {
            var point a, b;
            a = b;
         }
        """
        self.expect_errors(snippet, [11])


if __name__ == '__main__':
    unittest.main()

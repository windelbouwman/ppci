import unittest
import logging
import io
from ppci.c3 import Builder, Lexer
from ppci.target import SimpleTarget
from ppci import DiagnosticsManager, CompilerError


class testLexer(unittest.TestCase):
    def setUp(self):
        diag = DiagnosticsManager()
        self.l = Lexer(diag)

    def testUnexpectedCharacter(self):
        snippet = io.StringIO(""" var s \u6c34 """)
        with self.assertRaises(CompilerError):
            list(self.l.lex(snippet))

    def check(self, snippet, toks):
        toks2 = list(tok.typ for tok in self.l.lex(io.StringIO(snippet)))
        self.assertSequenceEqual(toks, toks2)

    def testBlockComment(self):
        snippet = """
          /* Demo */
          var int x = 0;
        """
        toks = ['var', 'ID', 'ID', '=', 'NUMBER', ';', 'EOF']
        self.check(snippet, toks)

    def testBlockCommentMultiLine(self):
        snippet = """
          /* Demo
          bla1
          bla2
          */
          var int x = 0;
        """
        toks = ['var', 'ID', 'ID', '=', 'NUMBER', ';', 'EOF']
        self.check(snippet, toks)


class testBuilder(unittest.TestCase):
    def setUp(self):
        self.diag = DiagnosticsManager()
        self.builder = Builder(self.diag, SimpleTarget())
        self.diag.clear()
        # Add a null logging handler to disable warning log messages:
        nh = logging.NullHandler()
        logging.getLogger().addHandler(nh)

    def makeFileList(self, snippet):
        """ Try to make a list with opened files """
        if type(snippet) is list:
            l2 = []
            for s in snippet:
                if type(s) is str:
                    l2.append(io.StringIO(s))
                else:
                    l2.append(s)
            return l2
        else:
            return [io.StringIO(snippet)]

    def expectErrors(self, snippet, rows):
        """ Helper to test for expected errors on rows """
        list(self.builder.build([io.StringIO(snippet)]))
        actualErrors = [err.row for err in self.diag.diags]
        if rows != actualErrors:
            self.diag.printErrors()
        self.assertSequenceEqual(rows, actualErrors)

    def expectOK(self, snippet):
        """ Expect a snippet to be OK """
        ircode = list(self.builder.build(self.makeFileList(snippet)))
        if len(self.diag.diags) > 0:
            self.diag.printErrors()
        self.assertTrue(all(ircode))
        self.assertEqual(0, len(self.diag.diags))
        return ircode

    def testPackage(self):
        p1 = """module p1;
        type int A;
        """
        p2 = """module p2;
        import p1;
        var p1.A b;
        """
        self.expectOK([p1, p2])

    def testPackageMutual(self):
        p1 = """module p1;
        import p2;
        type int A;
        var p2.B b;
        """
        p2 = """module p2;
        import p1;
        var p1.A a;
        """
        self.expectOK([p1, p2])

    def testConstant(self):
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
        self.expectOK(snip)

    def testConstantMutual(self):
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
        self.expectErrors(snip, [2])

    def testPackageNotExists(self):
        p1 = """module p1;
        import p23;
        """
        self.expectErrors(p1, [0])

    def testFunctArgs(self):
        snippet = """
         module testargs;
         function void t2(int a, double b)
         {
            t2(2, 2);
            t2(2);
            t2(1, 1.2);
         }
        """
        self.expectErrors(snippet, [5, 6])

    def testReturn(self):
        snippet = """
         module testreturn;
         function void t()
         {
            return;
         }
        """
        self.expectOK(snippet)

    def testReturn2(self):
        snippet = """
         module testreturn;
         function int t()
         {
            return 2;
         }
        """
        self.expectOK(snippet)

    def testExpressions(self):
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
        self.expectErrors(snippet, [8, 9])

    def testExpression1(self):
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
        self.expectOK(snippet)

    def testEmpty(self):
        snippet = """
        module A
        """
        self.expectErrors(snippet, [3])

    def testEmpty2(self):
        snippet = ""
        self.expectErrors(snippet, [1])

    def testRedefine(self):
        snippet = """
        module test;
        var int a;
        var int b;
        var int a;
        """
        self.expectErrors(snippet, [5])

    def testWhile(self):
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
        self.expectOK(snippet)

    def testWhile2(self):
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
        self.expectOK(snippet)

    def testIf(self):
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
        self.expectOK(snippet)

    def testAndCondition(self):
        snippet = """
        module tst;
        function void t() {
         if (4 > 3 and 1 < 10) {
         }
        }
        """
        self.expectOK(snippet)

    def testOrCondition(self):
        snippet = """
        module tst;
        function void t() {
         if (3 > 4 or 3 < 10) {
         }
        }
        """
        self.expectOK(snippet)

    def testNonBoolCondition(self):
        snippet = """
        module tst;
        function void t() {
         if (3+3) {
         }
        }
        """
        self.expectErrors(snippet, [4])

    def testTypeDef(self):
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
        self.expectOK(snippet)

    def testLocalVariable(self):
        snippet = """
         module testlocalvar;
         function void t()
         {
            var int a, b;
            a = 2;
            b = a + 2;
         }
        """
        self.expectOK(snippet)

    def testUnknownType(self):
        snippet = """module testlocalvar;
         function void t()
         {
            var int2 a;
         }
        """
        self.expectErrors(snippet, [4])

    def testStruct1(self):
        snippet = """
         module teststruct1;
         function void t()
         {
            var struct {int x, y;} a;
            a.x = 2;
            a.y = a.x + 2;
         }
        """
        self.expectOK(snippet)

    def testStruct2(self):
        """ Select struct member from non struct type """
        snippet = """
         module teststruct1;
         function void t() {
            var int a;
            a.z = 2;
         }
        """
        self.expectErrors(snippet, [5])

    def testArray(self):
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
        self.expectOK(snippet)

    def testArrayFail(self):
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
        self.expectErrors(snippet, [8])

    def testArrayFail2(self):
        snippet = """
         module testarray;
         function void t()
         {
            var int c;
            var int x;
            c = x[2];
         }
        """
        self.expectErrors(snippet, [7])

    def testArrayFail3(self):
        snippet = """
         module testarray;
         function void t()
         {
            var int[20] c;
         }
        """
        self.expectOK(snippet)

    def testStructCall(self):
        snippet = """
         module teststruct1;
         function void t()
         {
            var struct {int x, y;} a;
            a.x(9);
         }
        """
        self.expectErrors(snippet, [6])

    def testString(self):
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
        self.expectOK(snippet)

    def testSizeof1(self):
        snippet = """
         module testsizeof;

         function void t()
         {
            var int a;
            a = sizeof(int*);
         }
        """
        self.expectOK(snippet)

    def testSizeof2(self):
        snippet = """
         module testsizeof2;

         function void t()
         {
            sizeof(int*) = 2;
         }
        """
        self.expectErrors(snippet, [6])

    def testWrongVarUse(self):
        snippet = """
         module testsizeof;

         function void t()
         {
            var int a;
            a = 1;
         }
        """
        self.expectOK(snippet)

    def testPointerType1(self):
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
        self.expectOK(snippet)

    def testPointerType(self):
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
        self.expectOK(snippet)

    def testPointerTypeInCorrect(self):
        snippet = """
         module testpointerincorrect;
         var int* pa;
         function void t(int a, double b)
         {
            pa = 2; // type conflict
            pa = &a;
            pa = &2; // No valid lvalue
            &a = pa; // No valid lvalue
            **pa = 22; // Cannot deref int
         }
        """
        self.expectErrors(snippet, [6, 8, 9, 10])

    def testPointerTypeIr(self):
        snippet = """
         module testptr_ir;
         function void t()
         {
            var int* a;
            a = cast<int*>(40);
            *a = 2;
         }
        """
        self.expectOK(snippet)

    def testPointerTypeIr2(self):
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
        self.expectOK(snippet)

    def testPointerArithmatic(self):
        snippet = """
         module testpointerarithmatic;
         function void t()
         {
            var int* pa;
            *(pa+2) = 2;
         }
        """
        self.expectOK(snippet)

    def testWrongCast(self):
        snippet = """
         module testptr_ir;
         type struct {int x,y;}* gpio;
         function void t()
         {
            var gpio a;
            *cast<gpio>(*a);
         }
        """
        self.expectErrors(snippet, [7])

    def testLinkedList(self):
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
        self.expectOK(snippet)

    def testInfiniteStruct(self):
        """
            Test if a struct can contain a field with itself as type?
            This should not be possible!
        """
        snippet = """
         module testnestedstruct;

         type struct {
            int x;
            list_t inner;
         } list_t;

        """
        self.expectErrors(snippet, [0])

    def testMutualStructs(self):
        """
            Test if two structs can contain each other!
            This should not be possible!
        """
        snippet = """
         module testnestedstruct;

         type struct {
            int x;
            B other;
         } A;

         type struct {
            int x;
            A other;
         } B;

        """
        self.expectErrors(snippet, [0])

    def testComplexType(self):
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
        self.expectOK(snippet)


if __name__ == '__main__':
    unittest.main()

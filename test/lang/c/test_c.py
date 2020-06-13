import unittest
import io
from ppci.common import CompilerError
from ppci.lang.c import CBuilder, render_ast, print_ast, COptions
from ppci.arch.example import ExampleArch
from ppci import ir
from ppci.irutils import verify_module


class CFrontendTestCase(unittest.TestCase):
    """ Test if various C-snippets build correctly """

    def setUp(self):
        arch = ExampleArch()
        self.builder = CBuilder(arch.info, COptions())

    def do(self, src):
        self._do_compile(src)
        self._print_ast(src)

    def _do_compile(self, src):
        f = io.StringIO(src)
        try:
            ir_module = self.builder.build(f, None)
        except CompilerError as compiler_error:
            lines = src.split("\n")
            compiler_error.render(lines)
            raise
        assert isinstance(ir_module, ir.Module)
        verify_module(ir_module)

    def _print_ast(self, src):
        # Try to parse ast as well:
        tree = self.builder._create_ast(src, None)
        print(tree)
        print("C-AST:")
        print_ast(tree)

        # Print rendered c:
        print("re-rendered C:")
        render_ast(tree)

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

    def test_for_statement(self):
        src = """
        int main() {
            int i;
            for (i=i;i<10;i++) { }
            for (i=0;;) { }
            for (;;) { }
            for (int x=0;x<10;x++) { }
        }
        """
        self.do(src)

    def test_for_statement_scope(self):
        """ Test the scope of declarations inside a for loop. """
        src = """
        void print(int);
        int main() {
            for (int i=0;i<10;i++) print(i);
            for (int i=0;i<10;i++) print(i);
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

    def test_ternary_operator(self):
        """ Test ternary operator with functions. """
        src = """
        int foo(int x) { return x + 1; }
        int bar(int x) { return x - 1; }
        void p1(int x);
        void p2(int x);

        void main(int b) {
          int a;
          a = (b ? foo : bar)(22); // ternary usage with function pointers
          (b ? p1 : p2)(33);  // ternary usage with void type
        }
        """
        self.do(src)

    def test_comma_operator(self):
        """ Test comma operator """
        src = """
        void main() {
          int a,b,c,d;
          a = 2, b=3;
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
        struct {} empty_unit;
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

    def test_tag_scoping(self):
        src = """
        void f(int n) {
          struct S { int a; } s;
          union U { int a; } u;
          enum E { E1, E2 } e;
          if (n == 10) {
              struct S { int b; } s;
              s.b = 1;
              union U { int b; } u;
              u.b = 1;
              enum E { E3, E4 } e;
              e = E3;
          }
          s.a = 2;
          u.a = 2;
          e = E1;
        }
        """
        self.do(src)

    def test_struct_copy(self):
        """ Test struct behavior when copied around. """
        src = """
        typedef struct {int a,b,c,d,e,f; } data_t;
        data_t my_f(data_t y) {
            data_t z;
            z.a = y.a;
            z.b = 42;
          return z;
        }
        void main() {
            data_t *ptr;
            data_t x;
            x = *ptr++;
            x = my_f(x);
            x = my_f(*ptr--);
        }
        """
        self.do(src)

    def test_bad_bitfield_type(self):
        """ Test bad bitfield type """
        src = """
        struct z { float foo : 3; };
        """
        self.expect_errors(src, [(2, r"Invalid type \(float\) for bit-field")])

    def test_offsetof(self):
        """ Test offsetof """
        src = """
        struct z { int foo; };
        void main() {
             __builtin_offsetof(struct z, foo);
        }
        """
        self.do(src)

    def test_offsetof_after_bitfield(self):
        """ Test offsetof after bitfields works """
        src = """
        struct z { char foo : 1; int fu : 2; int bar; };
        void do_x(struct z g) {
        }

        void main() {
             __builtin_offsetof(struct z, bar);
             struct z y;
             do_x(y);
        }
        """
        self.do(src)

    def test_offsetof_bitfield(self):
        """ Test offsetof on bitfields returns an error """
        src = """
        struct z { int foo : 23; };
        void main() {
         __builtin_offsetof(struct z, foo);
        }
        """
        self.expect_errors(src, [(4, 'address of bit-field "foo"')])

    def test_union(self):
        """ Test union usage """
        src = """
        union z { int foo; struct { int b, a, r; } bar;};
        union z myZ[2] = {1, 2};
        void main() {
          union z localZ[2] = {1, 2};
        }
        """
        self.do(src)

    def test_anonymous_union_member(self):
        """ Test anonymous union member access. """
        src = """
        union z { int foo; struct { int b; }; };
        void main() {
          union z my_z;
          my_z.b = 34;
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

    def test_pointer_arithmatics(self):
        """ Test dark pointer voodoo """
        src = """
        void main() {
         int *a, b, *c;
         a = &b;
         c = a + 10;  // pointer + numeric
         c = 20 + a;  // numeric + pointer
         a = a - 10;  // pointer - numeric
         b = c - a;   // pointer - pointer
         a += 2;
         a -= 4;
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
        self.expect_errors(src, [(3, "Wrong tag kind")])

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

    def test_enum_implicit_cast(self):
        """ Test enum casting """
        src = """
        void main() {
         enum E { A, B, C };
         enum D { X, Y, Z };
         enum E e = Z;
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
         s = &"bla"[2]; // This is fine!
        }
        """
        self.do(src)

    def test_compound_literal(self):
        """ Test compund literal """
        src = """
        typedef struct { int x; } X_t;

        X_t main() {
         return (X_t){2};
        }
        """
        self.do(src)

    def test_global_compound_literal(self):
        """ Test pointer to global compund literals.

        Points of interest:
        - compound literals can empty initializer lists.
        """
        src = """
        int *pa1 = (int[]){1,2,3,4};
        int *pa2 = (int[4]){1,2,3,4};
        struct S2 { int a; };
        struct S2* ps1 = &((struct S2){.a=2});
        struct S2* ps2 = &((struct S2){});
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

    def test_switch_gnu(self):
        """ Test switch statement with gnu extension. """
        src = """
        void main() {
          int b = 23;
          switch (b) {
            case 34 ... 40:
              b = 1;
              break;
            case 342:
              b = 2;
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
        self.expect_errors(src, [(3, "Case statement outside")])

    def test_loose_default(self):
        """ Test loose default statement """
        src = """
        void main() {
          default: break;
        }
        """
        self.expect_errors(src, [(3, "Default statement outside")])

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

    def test_function_argument_name(self):
        """ Test an argument name with the same name as a typedef """
        src = """
        typedef double a;
        void add(a a) {
          a: return;
        }
        void mul(int a) {
          unsigned int a;
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

    def test_afterwards_declaration(self):
        """ Test redeclaration """
        src = """
        char a = 2;
        extern char a;  // this is fine too!
        char a;  // this is fine

        int add(int a, int b);
        int add(int a, int b); // fine!
        int add(int a, int b) {
          return a + b;
        }
        int add(int a, int b); // fine!

        """
        self.do(src)

    def test_variable_double_definition(self):
        """ Test double definition raises an error. """
        src = """
        char a = 2;
        char a = 3; // Not cool!
        """
        self.expect_errors(src, [(3, "Invalid redefinition")])

    def test_function_double_definition(self):
        """ Test double definition raises an error. """
        src = """
        int add(int a, int b) {
          return a + b;
        }
        int add(int a, int b) { // Not cool!
          return a + b;
        }
        """
        self.expect_errors(src, [(5, "invalid redefinition")])

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

    def test_initialization(self):
        """ Test initialization of complex data structures. """
        src = """
        struct rec {
          int a, b;
          char c[5];
          struct {
            int x, y;
          } d;
        };
        char x = '\2';
        int* ptr = (int*)0x1000;
        int data;
        int* ptr2 = &data;
        struct rec d = {.b = 2, .c = {[2] = 3}, .d.x=100};
        int e[] = {1, [2]=3, [0] = 2, [6]=2.2};
        int f[] = {1,2,[5]=6};

        void main() {
            char x = '\2';
            int* ptr = (int*)0x1000;
            struct rec d = {.b = 2, .c = {[2] = 3}, .d.x=100};
            int e[] = {1, [2]=3, [0] = 2, [6]=2.2};
            int f[] = {1,2,[5]=6};
        }
        """
        self.do(src)

    def test_anonymous_struct_field_initialization(self):
        """ Test designated initialization into an anonymous struct. """
        src = """
        struct rec {
          struct {
            int x;
          };
        };
        struct rec d = {.x = 2};
        void main() {
            struct rec d = {.x = 2};
        }
        """
        self.do(src)

    def test_function_pointer_passing(self):
        """ Test passing of function pointers """
        src = """

        void callback(void)
        {
        }

        static void (*cb)(void);
        void register_callback(void (*f)())
        {
          cb = f;
        }

        void main() {
          register_callback(callback);
          callback(); // direct call
          cb();  // via function pointer
          // TODO: (*cb)();  // again via function pointer
        }
        """
        self.do(src)

    def test_not_all_paths_return_value(self):
        """ Test what happens when not all code paths return a value """
        src = """
        int f(int a)
        {
          if(a == 0) return(1);
        }
        """
        self.do(src)

    def test_array_of_strings(self):
        """ Test array's of strings """
        src = """
        char *msg[] = {
          "Hi",
          "Bonjour"
        };
        """
        self.do(src)

    def test_inline_asm(self):
        """ Test inline assembly code. """
        src = """
        void main(int a) {
          // This is example arch asm code:
          int res;
          asm (
            "add r0, r1, r2"
            : // TODO: "=r" (res)
            : "r" (a)
          );
        }
        """
        self.do(src)


if __name__ == "__main__":
    unittest.main()

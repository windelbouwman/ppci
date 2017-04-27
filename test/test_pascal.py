import unittest
import io
from ppci.lang.pascal import PascalBuilder
from ppci.arch.example import ExampleArch
from ppci.common import DiagnosticsManager, CompilerError
from ppci.irutils import Verifier
from ppci.binutils.debuginfo import DebugDb


class BuildTestCaseBase(unittest.TestCase):
    """ Test if various snippets build correctly """
    def setUp(self):
        self.diag = DiagnosticsManager()
        self.builder = PascalBuilder(self.diag, ExampleArch(), DebugDb())
        self.diag.clear()

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
        ir_modules = self.builder.build(srcs)
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
        # TODO:
        # self.assertTrue(ircode)
        verifier = Verifier()
        for mod in ircode:
            verifier.verify(mod)
        self.assertEqual(0, len(self.diag.diags))


class PascalTestCase(BuildTestCaseBase):
    """ Test pascal snippets """

    def test_hello(self):
        """ Test the pascal hello world """
        snippet = """
        {
          This is a hello world program with nice comments!
        }
        program hello1;

        begin
          writeln('Hello world!')
        end.
        """
        self.expect_ok(snippet)

    def test_if(self):
        """ Test if statement """
        snippet = """
        program test_if;
        var
         { Local variable }
         a: integer;

        begin
          a := 100;
          if (a < 20) then
            (* check something *)
            writeln('A is less than 20')
          else if (a = 33) then
            writeln('A is 33')
          else
            writeln('A more than 20 or 20 and not 33')
        end.
        """
        self.expect_ok(snippet)

    def test_for_loop(self):
        """ Test the for loop """
        snippet = """
        program hello1;
        var
         a: integer;

        begin
          for a := 10 to 20 do

          begin
            writeln('Hello world!', a);
          end;
        end.
        """
        self.expect_ok(snippet)

    def test_case_else(self):
        """ Test case followed by else """
        snippet = """
        program test_case_else;
        var
         grade: char;

        begin
          grade := 'F';
          case (grade) of
           'A': writeln('Excellent!');
           'B', 'C': writeln('Well done!');
           'D': writeln('Passed');
          else
            writeln('Too bad...');
          end;

          writeln('Your grade is', grade);
        end.
        """
        self.expect_ok(snippet)


if __name__ == '__main__':
    unittest.main()

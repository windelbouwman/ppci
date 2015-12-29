import unittest
import tempfile
import io

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from ppci.commands import c3c, build, asm, hexutil, yacc_cmd, objdump
from ppci.common import DiagnosticsManager, SourceLocation
from util import relpath


class BuildTestCase(unittest.TestCase):
    """ Test the build command-line utility """
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_build_command(self, mock_stderr):
        """ Test normal use """
        _, report_file = tempfile.mkstemp()
        build_file = relpath('..', 'examples', 'build.xml')
        build(['-v', '--report', report_file, '-f', build_file])

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_help(self, mock_stdout):
        """ Test help function """
        with self.assertRaises(SystemExit) as cm:
            build(['-h'])
        self.assertEqual(0, cm.exception.code)
        self.assertIn('build', mock_stdout.getvalue())

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_invalid_log_level(self, mock_stderr):
        """ Test invalid log level """
        with self.assertRaises(SystemExit) as cm:
            build(['--log', 'blabla'])
        self.assertEqual(2, cm.exception.code)
        self.assertIn('invalid log_level value', mock_stderr.getvalue())


class C3cTestCase(unittest.TestCase):
    """ Test the c3c command-line utility """
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_c3c_command_fails(self, mock_stdout, mock_stderr):
        c3_file = relpath('..', 'examples', 'snake', 'game.c3')
        with self.assertRaises(SystemExit) as cm:
            c3c(['--target', 'arm', c3_file])
        self.assertEqual(1, cm.exception.code)

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_c3c_command_succes(self, mock_stdout, mock_stderr):
        """ Capture stdout. Important because it is closed by the command! """
        c3_file = relpath('..', 'examples', 'stm32f4', 'bsp.c3')
        c3c(['--target', 'arm', c3_file])

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_c3c_command_help(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            c3c(['-h'])
        self.assertEqual(0, cm.exception.code)
        self.assertIn('compiler', mock_stdout.getvalue())


class AsmTestCase(unittest.TestCase):
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_asm_command(self, mock_stderr):
        _, obj_file = tempfile.mkstemp()
        src = relpath('..', 'examples', 'lm3s6965', 'startup.asm')
        asm(['--target', 'thumb', '-o', obj_file, src])

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_help(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            asm(['-h'])
        self.assertEqual(0, cm.exception.code)
        self.assertIn('assemble', mock_stdout.getvalue())


class ObjdumpTestCase(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_help(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            objdump(['-h'])
        self.assertEqual(0, cm.exception.code)
        self.assertIn('object file', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_command(self, mock_stdout):
        _, obj_file = tempfile.mkstemp()
        src = relpath('..', 'examples', 'lm3s6965', 'startup.asm')
        asm(['--target', 'thumb', '-o', obj_file, src])
        objdump([obj_file])
        self.assertIn('SECTION', mock_stdout.getvalue())


class HexutilTestCase(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_hexutil_help(self, mock_stdout):
        """ Check hexutil help message """
        with self.assertRaises(SystemExit) as cm:
            hexutil(['-h'])
        self.assertEqual(0, cm.exception.code)
        self.assertIn('info,new,merge', mock_stdout.getvalue())

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_hexutil_address_format(self, mock_stderr):
        _, file1 = tempfile.mkstemp()
        datafile = relpath('..', 'examples', 'build.xml')
        with self.assertRaises(SystemExit) as cm:
            hexutil(['new', file1, '10000000', datafile])
        self.assertEqual(2, cm.exception.code)
        self.assertIn('argument address', mock_stderr.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_hexutil_no_command(self, mock_stdout):
        """ No command given """
        with self.assertRaises(SystemExit) as cm:
            hexutil([])
        self.assertNotEqual(0, cm.exception.code)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_hexutil_merge(self, mock_stdout):
        """ Create three hexfiles and manipulate those """
        _, file1 = tempfile.mkstemp()
        _, file2 = tempfile.mkstemp()
        _, file3 = tempfile.mkstemp()
        datafile = relpath('..', 'docs', 'logo', 'logo.png')
        hexutil(['new', file1, '0x10000000', datafile])
        hexutil(['new', file2, '0x20000000', datafile])
        hexutil(['merge', file1, file2, file3])
        hexutil(['info', file3])
        self.assertIn("Hexfile containing 2832 bytes", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_hexutil_info(self, mock_stdout):
        """ Create three hexfiles and manipulate those """
        _, file1 = tempfile.mkstemp()
        datafile = relpath('..', 'docs', 'logo', 'logo.png')
        hexutil(['new', file1, '0x10000000', datafile])
        hexutil(['info', file1])
        self.assertIn("Hexfile containing 1416 bytes", mock_stdout.getvalue())


class YaccTestCase(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_help(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            yacc_cmd(['-h'])
        self.assertEqual(0, cm.exception.code)
        self.assertIn('compiler compiler', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_normal_use(self, mock_stdout):
        """ Test normal yacc use """
        grammar_file = relpath('..', 'ppci', 'burg.grammar')
        yacc_cmd([grammar_file])
        self.assertIn('Automatically generated', mock_stdout.getvalue())


class DiagnosticsTestCase(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_error_reporting(self, mock_stdout):
        """ Simulate some errors into the diagnostics system """
        filename = relpath('..', 'examples', 'snake', 'game.c3')
        diag = DiagnosticsManager()
        with open(filename, 'r') as f:
            src = f.read()
        diag.add_source(filename, src)
        diag.error('Test1', SourceLocation(filename, 1, 2, 1))
        diag.error('Test2', SourceLocation(filename, 1000, 2, 1))
        diag.error('Test2', SourceLocation("other.c", 1000, 2, 1))
        diag.error('Test3', None)
        diag.print_errors()

    def test_error_repr(self):
        diag = DiagnosticsManager()
        diag.error('A', None)
        self.assertTrue(str(diag.diags))


if __name__ == '__main__':
    unittest.main()

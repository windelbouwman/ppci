import unittest
import shlex
import tempfile
import io
from unittest.mock import patch
from ppci.commands import c3c, build, asm, hexutil
from ppci.common import DiagnosticsManager, SourceLocation
from util import relpath


class CommandsTestCase(unittest.TestCase):
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_build_command(self, mock_stderr):
        _, report_file = tempfile.mkstemp()
        build_file = relpath('..', 'examples', 'build.xml')
        build(shlex.split(
            '-v --report {} -f {}'.format(report_file, build_file)))

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_build_command_help(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            build(shlex.split('-h'))
        self.assertEqual(0, cm.exception.code)
        self.assertIn('build', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_c3c_command_fails(self, mock_stdout, mock_stderr):
        c3_file = relpath('..', 'examples', 'snake', 'game.c3')
        with self.assertRaises(SystemExit) as cm:
            c3c(shlex.split('--target arm {}'.format(c3_file)))
        self.assertEqual(1, cm.exception.code)

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_c3c_command_succes(self, mock_stdout, mock_stderr):
        """ Capture stdout. Important because it is closed by the command! """
        c3_file = relpath('..', 'examples', 'stm32f4', 'bsp.c3')
        c3c(shlex.split('--target arm {}'.format(c3_file)))

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_c3c_command_help(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            c3c(shlex.split('-h'))
        self.assertEqual(0, cm.exception.code)
        self.assertIn('compiler', mock_stdout.getvalue())

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_asm_command(self, mock_stderr):
        _, obj_file = tempfile.mkstemp()
        src = relpath('..', 'examples', 'lm3s6965', 'startup.asm')
        asm(shlex.split('--target thumb -o {} {}'.format(obj_file, src)))

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_asm_command_help(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            asm(shlex.split('-h'))
        self.assertEqual(0, cm.exception.code)
        self.assertIn('assemble', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_hexutil_help(self, mock_stdout):
        """ Check hexutil help message """
        with self.assertRaises(SystemExit) as cm:
            hexutil(shlex.split('-h'))
        self.assertEqual(0, cm.exception.code)
        self.assertIn('info,new,merge', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_hexutil_no_command(self, mock_stdout):
        """ No command given """
        with self.assertRaises(SystemExit) as cm:
            hexutil(shlex.split(''))
        self.assertEqual(1, cm.exception.code)
        self.assertIn('info,new,merge', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_hexutil(self, mock_stdout):
        """ Create three hexfiles and manipulate those """
        _, file1 = tempfile.mkstemp()
        _, file2 = tempfile.mkstemp()
        _, file3 = tempfile.mkstemp()
        datafile = relpath('..', 'examples', 'build.xml')
        hexutil(shlex.split('new {} 0x10000000 {}'.format(file1, datafile)))
        hexutil(shlex.split('info {}'.format(file1)))
        hexutil(shlex.split('new {} 0x20000000 {}'.format(file2, datafile)))
        hexutil(shlex.split('merge {} {} {}'.format(file1, file2, file3)))


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
        diag.error('Test3', None)
        diag.print_errors()

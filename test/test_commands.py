import unittest
import shlex
import tempfile
from ppci.commands import c3c, build, asm, hexutil
from ppci.common import DiagnosticsManager, SourceLocation


class CommandsTestCase(unittest.TestCase):
    def test_build_command(self):
        _, report_file = tempfile.mkstemp()
        build(shlex.split(
            '-v --report {} -f examples/build.xml'.format(report_file)))

    def test_build_command_help(self):
        with self.assertRaises(SystemExit) as cm:
            build(shlex.split('-h'))
        self.assertEqual(0, cm.exception.code)

    def test_c3c_command(self):
        with self.assertRaises(SystemExit) as cm:
            c3c(shlex.split('--target arm examples/snake/game.c3'))
        self.assertEqual(1, cm.exception.code)

    def test_c3c_command_help(self):
        with self.assertRaises(SystemExit) as cm:
            c3c(shlex.split('-h'))
        self.assertEqual(0, cm.exception.code)

    def test_asm_command(self):
        _, obj_file = tempfile.mkstemp()
        src = 'examples/lm3s6965/startup.asm'
        asm(shlex.split('--target thumb -o {} {}'.format(obj_file, src)))

    def test_asm_command_help(self):
        with self.assertRaises(SystemExit) as cm:
            asm(shlex.split('-h'))
        self.assertEqual(0, cm.exception.code)

    def test_hexutil_help(self):
        with self.assertRaises(SystemExit) as cm:
            hexutil(shlex.split('-h'))
        self.assertEqual(0, cm.exception.code)


class DiagnosticsTestCase(unittest.TestCase):
    def test_error_reporting(self):
        """ Simulate some errors into the diagnostics system """
        filename = 'examples/snake/game.c3'
        diag = DiagnosticsManager()
        with open(filename, 'r') as f:
            src = f.read()
        diag.add_source(filename, src)
        diag.error('Test1', SourceLocation(filename, 1, 2, 1))
        diag.error('Test2', SourceLocation(filename, 1000, 2, 1))
        diag.error('Test3', None)
        diag.print_errors()

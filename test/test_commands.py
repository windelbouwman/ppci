import unittest
import shlex
import tempfile
from ppci.commands import c3c, build, asm


class CommandsTestCase(unittest.TestCase):
    def test_build_command(self):
        _, report_file = tempfile.mkstemp()
        build(shlex.split(
            '-v --report {} -f examples/build.xml'.format(report_file)))

    def test_build_command_help(self):
        with self.assertRaises(SystemExit) as cm:
            build(shlex.split('-h'))
        self.assertEqual(0, cm.exception.code)

    def test_c3c_command_help(self):
        with self.assertRaises(SystemExit) as cm:
            c3c(shlex.split('-h'))
        self.assertEqual(0, cm.exception.code)

    def test_asm_command_help(self):
        with self.assertRaises(SystemExit) as cm:
            asm(shlex.split('-h'))
        self.assertEqual(0, cm.exception.code)

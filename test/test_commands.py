""" Test cases for the various commandline utilities. """

import unittest
import tempfile
import io
import os
from unittest.mock import patch

from ppci.cli.asm import asm
from ppci.cli.build import build
from ppci.cli.c3c import c3c
from ppci.cli.cc import cc
from ppci.cli.hexdump import hexdump
from ppci.cli.java import java
from ppci.cli.link import link
from ppci.cli.objdump import objdump
from ppci.cli.objcopy import objcopy
from ppci.cli.ocaml import ocaml
from ppci.cli.opt import opt
from ppci.cli.pascal import pascal
from ppci.cli.yacc import yacc
from ppci import api
from ppci.common import DiagnosticsManager, SourceLocation
from ppci.binutils.objectfile import ObjectFile, Section, Image
from helper_util import relpath, do_long_tests


def new_temp_file(suffix):
    """ Generate a new temporary filename """
    handle, filename = tempfile.mkstemp(suffix=suffix)
    os.close(handle)
    return filename


@unittest.skipUnless(do_long_tests('any'), 'skipping slow tests')
class BuildTestCase(unittest.TestCase):
    """ Test the build command-line utility """
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_build_command(self, mock_stdout, mock_stderr):
        """ Test normal use """
        report_file = new_temp_file('.html')
        build_file = relpath(
            '..', 'examples', 'lm3s6965evb', 'snake', 'build.xml')
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


@unittest.skipUnless(do_long_tests('any'), 'skipping slow tests')
class C3cTestCase(unittest.TestCase):
    """ Test the c3c command-line utility """
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_c3c_command_fails(self, mock_stdout, mock_stderr):
        c3_file = relpath('..', 'examples', 'snake', 'game.c3')
        obj_file = new_temp_file('.obj')
        with self.assertRaises(SystemExit) as cm:
            c3c(['-m', 'arm', c3_file, '-o', obj_file])
        self.assertEqual(1, cm.exception.code)

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_c3c_command_succes(self, mock_stdout, mock_stderr):
        """ Capture stdout. Important because it is closed by the command! """
        c3_file = relpath('..', 'examples', 'stm32f4', 'bsp.c3')
        obj_file = new_temp_file('.obj')
        c3c(['-m', 'arm', c3_file, '-o', obj_file])

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_c3c_command_help(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            c3c(['-h'])
        self.assertEqual(0, cm.exception.code)
        self.assertIn('compiler', mock_stdout.getvalue())


class CcTestCase(unittest.TestCase):
    """ Test the cc command-line utility """
    c_file = relpath('..', 'examples', 'c', 'hello', 'std.c')

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_cc_command(self, mock_stdout, mock_stderr):
        """ Capture stdout. Important because it is closed by the command! """
        oj_file = new_temp_file('.oj')
        cc(['-m', 'arm', self.c_file, '-o', oj_file])

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_cc_command_s(self, mock_stdout, mock_stderr):
        """ Capture stdout. Important because it is closed by the command! """
        oj_file = new_temp_file('.oj')
        cc(['-m', 'arm', '-S', self.c_file, '-o', oj_file])

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_cc_command_e(self, mock_stdout, mock_stderr):
        """ Capture stdout. Important because it is closed by the command! """
        oj_file = new_temp_file('.oj')
        cc(['-m', 'arm', '-E', self.c_file, '-o', oj_file])

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_cc_command_ir(self, mock_stdout, mock_stderr):
        """ Capture stdout. Important because it is closed by the command! """
        oj_file = new_temp_file('.oj')
        cc(['-m', 'arm', '--ir', self.c_file, '-o', oj_file])

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cc_command_help(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            cc(['-h'])
        self.assertEqual(0, cm.exception.code)
        self.assertIn('compiler', mock_stdout.getvalue())


class PascalTestCase(unittest.TestCase):
    """ Test the pascal command-line program """
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_hello(self, mock_stdout, mock_stderr):
        """ Compile hello world.pas """
        hello_pas = relpath('..', 'examples', 'src', 'pascal', 'hello.pas')
        obj_file = new_temp_file('.obj')
        pascal(['-m', 'arm', '-o', obj_file, hello_pas])

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_help(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            pascal(['-h'])
        self.assertEqual(0, cm.exception.code)
        self.assertIn('compiler', mock_stdout.getvalue())


class AsmTestCase(unittest.TestCase):
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_asm_command(self, mock_stderr):
        obj_file = new_temp_file('.obj')
        src = relpath('..', 'examples', 'avr', 'arduino-blinky', 'boot.asm')
        asm(['-m', 'avr', '-o', obj_file, src])

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_help(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            asm(['-h'])
        self.assertEqual(0, cm.exception.code)
        self.assertIn('assemble', mock_stdout.getvalue())


@unittest.skipUnless(do_long_tests('any'), 'skipping slow tests')
class ObjdumpTestCase(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_help(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            objdump(['-h'])
        self.assertEqual(0, cm.exception.code)
        self.assertIn('object file', mock_stdout.getvalue())

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_command(self, mock_stderr):
        obj_file = new_temp_file('.obj')
        src = relpath('..', 'examples', 'avr', 'arduino-blinky', 'boot.asm')
        asm(['-m', 'avr', '-o', obj_file, src])
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            objdump([obj_file])
            self.assertIn('SECTION', mock_stdout.getvalue())


@unittest.skipUnless(do_long_tests('any'), 'skipping slow tests')
class ObjcopyTestCase(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_help(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            objcopy(['-h'])
        self.assertEqual(0, cm.exception.code)
        self.assertIn('format', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_command(self, mock_stdout, mock_stderr):
        obj_file = new_temp_file('.obj')
        bin_file = new_temp_file('.bin')
        arch = api.get_arch('arm')
        obj = ObjectFile(arch)
        data = bytes(range(100))
        section = Section('.text')
        section.add_data(data)
        image = Image('code2', 0)
        image.sections.append(section)
        obj.add_section(section)
        obj.add_image(image)
        with open(obj_file, 'w') as f:
            obj.save(f)
        objcopy(['-O', 'bin', '-S', 'code2', obj_file, bin_file])
        with open(bin_file, 'rb') as f:
            exported_data = f.read()
        self.assertEqual(data, exported_data)


class OptimizeCommandTestCase(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_help(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            opt(['-h'])
        self.assertEqual(0, cm.exception.code)

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_optimize_command(self, mock_stdout, mock_stderr):
        in_file = relpath('data', 'add.pi')
        out = new_temp_file('.ir')
        opt([in_file, out])


@unittest.skipUnless(do_long_tests('any'), 'skipping slow tests')
class LinkCommandTestCase(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_help(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            link(['-h'])
        self.assertEqual(0, cm.exception.code)
        self.assertIn('obj', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_command(self, mock_stdout, mock_stderr):
        obj1 = new_temp_file('.obj')
        obj2 = new_temp_file('.obj')
        obj3 = new_temp_file('.obj')
        asm_src = relpath('..', 'examples', 'lm3s6965evb', 'startup.asm')
        mmap = relpath('..', 'examples', 'lm3s6965evb', 'memlayout.mmap')
        c3_srcs = [
            relpath('..', 'examples', 'src', 'snake', 'main.c3'),
            relpath('..', 'examples', 'src', 'snake', 'game.c3'),
            relpath('..', 'librt', 'io.c3'),
            relpath('..', 'examples', 'lm3s6965evb', 'bsp.c3'),
            ]
        asm(['-m', 'arm', '--mtune', 'thumb', '-o', obj1, asm_src])
        c3c(['-m', 'arm', '--mtune', 'thumb', '-o', obj2] + c3_srcs)
        link(
            ['-o', obj3, '-L', mmap, obj1, obj2])


class YaccTestCase(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_help(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            yacc(['-h'])
        self.assertEqual(0, cm.exception.code)
        self.assertIn('Parser generator', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_normal_use(self, mock_stdout, mock_stderr):
        """ Test normal yacc use """
        grammar_file = relpath('..', 'ppci', 'codegen', 'burg.grammar')
        file1 = new_temp_file('.py')
        yacc([grammar_file, '-o', file1])
        with open(file1, 'r') as f:
            content = f.read()
        self.assertIn('Automatically generated', content)


class JavaTestCase(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_help(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            java(['-h'])
        self.assertEqual(0, cm.exception.code)
        self.assertIn('java', mock_stdout.getvalue())


class OcamlTestCase(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_help(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            ocaml(['-h'])
        self.assertEqual(0, cm.exception.code)
        self.assertIn('OCaml', mock_stdout.getvalue())


class HexDumpTestCase(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_help(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            hexdump(['-h'])
        self.assertEqual(0, cm.exception.code)
        self.assertIn('dump', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_dump(self, mock_stdout):
        bin_file = relpath('..', 'docs', 'logo', 'logo.png')
        hexdump([bin_file])


class DiagnosticsTestCase(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_error_reporting(self, mock_stdout):
        """ Simulate some errors into the diagnostics system """
        filename = relpath('..', 'examples', 'src', 'snake', 'game.c3')
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
    unittest.main(verbosity=2)

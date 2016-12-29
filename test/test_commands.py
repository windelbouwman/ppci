import unittest
import tempfile
import io
import os

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from ppci.commands import c3c, build, asm, hexutil, yacc_cmd, objdump, objcopy
from ppci.commands import link
from ppci.common import DiagnosticsManager, SourceLocation
from ppci.binutils.objectfile import ObjectFile, Section, Image
from ppci.api import get_arch
from util import relpath, do_long_tests


def new_temp_file(suffix):
    """ Generate a new temporary filename """
    handle, filename = tempfile.mkstemp(suffix=suffix)
    os.close(handle)
    return filename


@unittest.skipUnless(do_long_tests(), 'skipping slow tests')
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


@unittest.skipUnless(do_long_tests(), 'skipping slow tests')
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


@unittest.skipUnless(do_long_tests(), 'skipping slow tests')
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


@unittest.skipUnless(do_long_tests(), 'skipping slow tests')
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
        arch = get_arch('arm')
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


@unittest.skipUnless(do_long_tests(), 'skipping slow tests')
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


@unittest.skipUnless(do_long_tests(), 'skipping slow tests')
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
        file1 = new_temp_file('.hex')
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
        file1 = new_temp_file('file1.hex')
        file2 = new_temp_file('file2.hex')
        file3 = new_temp_file('file3.hex')
        datafile = relpath('..', 'docs', 'logo', 'logo.png')
        hexutil(['new', file1, '0x10000000', datafile])
        hexutil(['new', file2, '0x20000000', datafile])
        hexutil(['merge', file1, file2, file3])
        hexutil(['info', file3])
        self.assertIn("Hexfile containing 2832 bytes", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_hexutil_info(self, mock_stdout):
        file1 = new_temp_file('file1.hex')
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
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_normal_use(self, mock_stdout, mock_stderr):
        """ Test normal yacc use """
        grammar_file = relpath('..', 'ppci', 'codegen', 'burg.grammar')
        file1 = new_temp_file('.py')
        yacc_cmd([grammar_file, '-o', file1])
        with open(file1, 'r') as f:
            content = f.read()
        self.assertIn('Automatically generated', content)


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

import unittest
import tempfile
import io
import os
from unittest.mock import patch

from helper_util import relpath, do_long_tests
from ppci.cli.hexutil import hexutil


def new_temp_file(suffix):
    """ Generate a new temporary filename """
    handle, filename = tempfile.mkstemp(suffix=suffix)
    os.close(handle)
    return filename


@unittest.skipUnless(do_long_tests('any'), 'skipping slow tests')
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


if __name__ == '__main__':
    unittest.main(verbosity=2)

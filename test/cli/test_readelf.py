import unittest
import io
import os
from unittest.mock import patch

from ppci.cli.readelf import readelf


bash_path = '/usr/bin/bash'


class ReadelfTestCase(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_help(self, mock_stdout):
        """ Check readelf help message """
        with self.assertRaises(SystemExit) as cm:
            readelf(['-h'])
        self.assertEqual(0, cm.exception.code)

    @unittest.skipUnless(
        os.path.exists(bash_path), '{} does not exist'.format(bash_path))
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_bash(self, mock_stdout):
        """ Check readelf on /usr/bin/bash message """
        readelf(['-a', bash_path])


if __name__ == '__main__':
    unittest.main(verbosity=2)

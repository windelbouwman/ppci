import unittest
import io
from unittest.mock import patch

from ppci.cli.mkuimage import mkuimage


class MkUimageTestCase(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_mkuimage_help(self, mock_stdout):
        """ Check mkuimage help message """
        with self.assertRaises(SystemExit) as cm:
            mkuimage(['-h'])
        self.assertEqual(0, cm.exception.code)


if __name__ == '__main__':
    unittest.main(verbosity=2)

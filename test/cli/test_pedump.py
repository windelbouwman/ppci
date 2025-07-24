import unittest
import io
from unittest.mock import patch

from ppci.cli.pedump import pedump


class PedumpTestCase(unittest.TestCase):
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_pedump_help(self, mock_stdout):
        """Check pedump help message"""
        with self.assertRaises(SystemExit) as cm:
            pedump(["-h"])
        self.assertEqual(0, cm.exception.code)


if __name__ == "__main__":
    unittest.main(verbosity=2)

import unittest
from ppci.lang.c.utils import replace_escape_codes


class CUtilitiesTestCase(unittest.TestCase):
    def test_escape_strings(self):
        """Test string escape codes"""
        src = r"\' \" \? \\ \a \b \f \n \r \t \v \0 \001 \e"
        expected = "' \" ? \\ \a \b \f \n \r \t \v \0 \1 \x1b"
        result = replace_escape_codes(src)
        self.assertEqual(expected, result)

    def test_escape_unicode(self):
        """Test string escape unicodes"""
        src = r"H \xfe \u1234 \U00010123"
        expected = "H \xfe \u1234 \U00010123"
        result = replace_escape_codes(src)
        self.assertEqual(expected, result)

import unittest
from functools import reduce
import operator
from ppci.arch import get_arch
from ppci.lang.c import CContext, parse_type
from ppci.lang.c.options import COptions


@unittest.skip("fixme")
class CTypeInitializerTestCase(unittest.TestCase):
    """Test if C-types are correctly initialized"""

    def setUp(self):
        arch = get_arch("x86_64")
        coptions = COptions()
        self.context = CContext(coptions, arch.info)

    def pack_value(self, ty, value):
        mem = self.context.gen_global_ival(ty, value)
        return reduce(operator.add, mem)

    def test_int_array(self):
        """Test array initialization"""
        src = "short[4]"
        ty = parse_type(src, self.context)
        self.assertEqual(8, self.context.sizeof(ty))
        mem = self.pack_value(ty, [1, 2, 3, 4])
        self.assertEqual(bytes([1, 0, 2, 0, 3, 0, 4, 0]), mem)

    def test_struct(self):
        src = "struct { char x; short y; }"
        ty = parse_type(src, self.context)
        self.assertEqual(4, self.context.sizeof(ty))
        mem = self.pack_value(ty, [3, 4])
        self.assertEqual(bytes([3, 0, 4, 0]), mem)

    def test_packed_struct(self):
        """Check how a packed struct is initialized"""
        src = "struct { unsigned x: 5; short y : 10; }"
        ty = parse_type(src, self.context)
        self.assertEqual(2, self.context.sizeof(ty))
        mem = self.pack_value(ty, [5, 2])
        self.assertEqual(bytes([69, 0]), mem)

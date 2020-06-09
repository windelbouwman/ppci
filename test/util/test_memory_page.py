import unittest

from ppci.utils.memory_page import MemoryPage


class MemoryPageTestCase(unittest.TestCase):
    def test_memory_page(self):
        p = MemoryPage(200)
        p.seek(0)
        p.write(bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]))
        p.seek(2)
        data = p.read(3)
        self.assertEqual(data, bytes([3, 4, 5]))
        data = p.read(4)
        self.assertEqual(data, bytes([6, 7, 8, 9]))
        p.write(bytes([88, 89, 92]))
        p.seek(8)
        data = p.read(6)
        self.assertEqual(data, bytes([9, 88, 89, 92, 13, 0]))

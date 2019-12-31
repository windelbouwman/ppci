import unittest
import io
from ppci.lang.ocaml import read_file

minimal_bytecode = bytes([
    0x1, 0x0, 0x0, 0x0,
    # CODE length=4:
    0x43, 0x4f, 0x44, 0x45, 0x0, 0x0, 0x0, 0x4,
    # 1 section:
    0x0, 0x0, 0x0, 0x1,
    # Caml1999X023:
    0x43, 0x61, 0x6d, 0x6c, 0x31, 0x39, 0x39, 0x39, 0x58, 0x30, 0x32, 0x33,
])


class OCamlByteCodeTestCase(unittest.TestCase):
    def test_minimal_bytecode(self):
        module = read_file(io.BytesIO(minimal_bytecode))
        instructions = module['CODE']
        self.assertEqual(1, len(instructions))
        self.assertEqual('ACC1', instructions[0].name)


if __name__ == '__main__':
    unittest.main()

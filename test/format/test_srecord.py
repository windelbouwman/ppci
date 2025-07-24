import unittest
from ppci.format.srecord import SRecord


class SRecordTestCase(unittest.TestCase):
    def test_hdr_line(self):
        record = SRecord(0, 0, "HDR".encode("ascii"))
        self.assertEqual(record.to_line(), "S00600004844521B")

    def test_wiki_record(self):
        record = SRecord(5, 3, bytes())
        self.assertEqual(record.to_line(), "S5030003F9")
        record = SRecord(
            1,
            0x7AF0,
            bytes([0xA, 0xA, 0xD, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
        )
        self.assertEqual(
            record.to_line(), "S1137AF00A0A0D0000000000000000000000000061"
        )


if __name__ == "__main__":
    unittest.main()

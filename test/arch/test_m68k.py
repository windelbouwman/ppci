import unittest
from ..test_asm import AsmTestCaseBase


class ArmAssemblerTestCase(AsmTestCaseBase):
    """ARM-mode (not thumb-mode) instruction assembly test case"""

    march = "m68k"

    def test_add(self):
        self.feed("addb d2, d5")
        self.feed("addb (a3), d6")
        self.check("da02 dc13")

    def test_cmp(self):
        self.feed("cmpb d2, d5")
        self.feed("cmpb (a3), d6")
        self.check("ba02 bc13")

    def test_eor(self):
        self.feed("eorb d5, d2")
        self.feed("eorb d6, (a3)")
        self.check("bb02 bd13")

    def test_lea(self):
        self.feed("lea dosname, a1")
        self.feed("dosname: db 4")
        self.check("43fa 0002 04")

    def test_move(self):
        self.feed("moveb (a1), (a2)")
        self.feed("movel (a1), (a2)")
        self.feed("movew (34,a1), (a2)")
        self.feed("movew (34,a1), (22,a2)")
        self.check("1491 2491 34a90022 356900220016")

    def test_movea(self):
        """Test move to address register"""
        self.feed("moveal (4).W, a6")
        self.check("2c78 0004")

    def test_moveq(self):
        """Test move quick"""
        self.feed("moveq #36, d0")
        self.check("7024")

    def test_neg(self):
        self.feed("negb d5")
        self.feed("negb (a4)")
        self.check("4405 4414")

    def test_nop(self):
        self.feed("nop")
        self.check("4e71")

    def test_not(self):
        self.feed("notb d0")
        self.check("4600")

    def test_rts(self):
        self.feed("rts")
        self.check("4e75")


if __name__ == "__main__":
    unittest.main()

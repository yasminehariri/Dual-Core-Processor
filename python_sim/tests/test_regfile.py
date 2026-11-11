"""test_regfile.py - mirrors tb/tb_regfile.v (23 checks)."""
import unittest

from python_sim.regfile import RegisterFile


class TestRegfile(unittest.TestCase):
    def test_tb_regfile(self):
        rf = RegisterFile()
        rf.regs = [0xAA] * 8                       # garbage, then reset
        rf.reset()
        self.assertEqual(rf.dbg()[0], 0x00, "reset clears R0")
        self.assertEqual(rf.dbg()[7], 0x00, "reset clears R7")

        for i in range(8):                         # write a different value into every register
            rf.write(i, 0x10 + i * 0x11, 1)
        for i in range(8):                         # read back on both ports
            self.assertEqual(rf.read(i), (0x10 + i * 0x11) & 0xFF, "read port 1 after write")
            self.assertEqual(rf.read(7 - i), (0x10 + (7 - i) * 0x11) & 0xFF, "read port 2 after write")

        rf.write(3, 0xEE, 0)
        self.assertEqual(rf.read(3), 0x43, "we=0 blocks write")

        # read-during-write: the combinational read before the edge sees the old value
        self.assertEqual(rf.read(1), 0x21, "read before write edge (old)")
        rf.write(1, 0x55, 1)                       # the edge
        self.assertEqual(rf.read(1), 0x55, "read after write edge (new)")

        rf.reset()
        self.assertEqual(rf.dbg()[1], 0x00, "second reset clears R1")
        self.assertEqual(rf.dbg()[5], 0x00, "second reset clears R5")


if __name__ == "__main__":
    unittest.main()

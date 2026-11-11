"""test_pc_unit.py - mirrors tb/tb_pc_unit.v (17 checks), same stimulus order."""
import unittest

from python_sim.pc_unit import PCUnit


class TestPCUnit(unittest.TestCase):
    def test_tb_pc_unit(self):
        p = PCUnit()
        p.pc, p.halted = 0x77, 1                              # garbage before reset

        def step(rst=0, halt=0, jump=0, bt=0, ja=0, off=0):
            p.clock(rst, halt, jump, bt, ja, off)

        step(rst=1)
        self.assertEqual((p.pc, p.halted), (0x00, 0), "reset gives 0, not halted")
        step(); self.assertEqual(p.pc, 0x01, "increment to 1")
        step(); self.assertEqual(p.pc, 0x02, "increment to 2")
        step(jump=1, ja=0x10); self.assertEqual(p.pc, 0x10, "jump to 0x10")
        step(bt=1, off=2); self.assertEqual(p.pc, 0x13, "branch +2 from 0x10 -> 0x13")
        step(bt=1, off=0b111110); self.assertEqual(p.pc, 0x12, "branch -2 -> 0x12")
        step(bt=1, off=0b100000); self.assertEqual(p.pc, 0xF3, "branch -32 wraps -> 0xF3")
        step(bt=1, off=0b011111); self.assertEqual(p.pc, 0x13, "branch +31 wraps -> 0x13")
        step(jump=1, ja=0xFF)
        step(); self.assertEqual(p.pc, 0x00, "wrap 0xFF -> 0x00")
        step(jump=1, bt=1, ja=0x40, off=5); self.assertEqual(p.pc, 0x40, "jump wins over branch")
        step(halt=1, jump=1, ja=0x99)
        self.assertEqual((p.pc, p.halted), (0x40, 1), "halt holds PC (beats jump), halted set")
        step(); step()
        self.assertEqual((p.pc, p.halted), (0x40, 1), "still held after halt")
        step(rst=1)
        self.assertEqual((p.pc, p.halted), (0x00, 0), "reset after halt gives 0, clears halted")


if __name__ == "__main__":
    unittest.main()

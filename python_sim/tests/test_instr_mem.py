"""test_instr_mem.py - mirrors tb/tb_instr_mem.v (19 checks)."""
import unittest

from python_sim.instr_mem import InstructionMemory
from python_sim.tests import prog

EXPECTED = [0x0650, 0x18C8, 0x2A50, 0x3A50, 0x4850, 0x5CE0, 0x6650, 0x7650,
            0x8220, 0x9640, 0xA205, 0xB4BF, 0xC63E, 0xD283, 0xE010, 0xF000]


class TestInstrMem(unittest.TestCase):
    def test_tb_instr_mem(self):
        im = InstructionMemory(prog("test_encodings.hex"))
        for i, exp in enumerate(EXPECTED):
            self.assertEqual(im.read(i), exp, f"program word {i}")
        for a in (16, 128, 255):
            self.assertEqual(im.read(a), 0xF000, f"unused address {a} is HALT")


if __name__ == "__main__":
    unittest.main()

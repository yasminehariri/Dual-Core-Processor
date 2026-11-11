"""test_control_unit.py - mirrors tb/tb_control_unit.v: all 16 opcodes + decoder fields."""
import unittest

from python_sim.control_unit import control
from python_sim.decoder import decode

# Copied from tb_control_unit.v:  RW AS ALUOp MR MW WB R2 Br NE J H
TABLE = [
    ("ADD", 0b0000, "1_0_000_0_0_00_0_0_0_0_0"),
    ("SUB", 0b0001, "1_0_001_0_0_00_0_0_0_0_0"),
    ("AND", 0b0010, "1_0_010_0_0_00_0_0_0_0_0"),
    ("OR", 0b0011, "1_0_011_0_0_00_0_0_0_0_0"),
    ("XOR", 0b0100, "1_0_100_0_0_00_0_0_0_0_0"),
    ("NOR", 0b0101, "1_0_101_0_0_00_0_0_0_0_0"),
    ("SLL", 0b0110, "1_0_110_0_0_00_0_0_0_0_0"),
    ("SRL", 0b0111, "1_0_111_0_0_00_0_0_0_0_0"),
    ("LOAD", 0b1000, "1_0_000_1_0_01_0_0_0_0_0"),
    ("STORE", 0b1001, "0_0_000_0_1_00_1_0_0_0_0"),
    ("LI", 0b1010, "1_0_000_0_0_10_0_0_0_0_0"),
    ("ADDI", 0b1011, "1_1_000_0_0_00_0_0_0_0_0"),
    ("BEQ", 0b1100, "0_0_001_0_0_00_1_1_0_0_0"),
    ("BNE", 0b1101, "0_0_001_0_0_00_1_1_1_0_0"),
    ("JMP", 0b1110, "0_0_000_0_0_00_0_0_0_1_0"),
    ("HALT", 0b1111, "0_0_000_0_0_00_0_0_0_0_1"),
]


class TestControlUnit(unittest.TestCase):
    def test_all_16_opcodes(self):
        for name, op, exp in TABLE:
            with self.subTest(name):
                self.assertEqual(control(op).bits(), int(exp.replace("_", ""), 2))

    def test_decoder_fields(self):
        f = decode(0x0650)                               # ADD R3, R1, R2
        self.assertEqual((f.opcode, f.rd, f.rs, f.rt), (0, 3, 1, 2))
        self.assertEqual(decode(0xB4BF).imm6_sext, 0xFF)  # ADDI R2, R2, -1
        self.assertEqual(decode(0xB490).imm6_sext, 0x10)  # +16
        self.assertEqual(decode(0xB4A0).imm6_sext, 0xE0)  # -32
        self.assertEqual(decode(0xC63E).off6, 0x3E)       # BEQ R3, R0, -2
        self.assertEqual(decode(0x9640).addr8, 0x40)      # STORE R3, [0x40]


if __name__ == "__main__":
    unittest.main()

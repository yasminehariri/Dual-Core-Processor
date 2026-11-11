"""test_alu.py - mirrors tb/tb_alu.v, plus an exhaustive 8 ops x 256 x 256 sweep.

The exhaustive reference below is written from the spec rules using ordinary
signed/unsigned arithmetic - NOT the 9-bit-adder trick alu.py uses - so the
two are independent.
"""
import unittest

from python_sim.alu import ALU, OP_ADD, OP_SUB, OP_AND, OP_OR, OP_XOR, OP_NOR, OP_SLL, OP_SRL


def signed8(x: int) -> int:
    return x - 256 if x & 0x80 else x


def reference(a: int, b: int, op: int) -> tuple[int, int, int, int]:
    """Spec rules, computed the 'obvious' way."""
    c = v = 0
    if op == OP_ADD:
        r = (a + b) & 0xFF
        c = int(a + b > 0xFF)
        v = int(not -128 <= signed8(a) + signed8(b) <= 127)
    elif op == OP_SUB:
        r = (a - b) & 0xFF
        c = int(a < b)                                    # borrow
        v = int(not -128 <= signed8(a) - signed8(b) <= 127)
    elif op == OP_AND:
        r = a & b
    elif op == OP_OR:
        r = a | b
    elif op == OP_XOR:
        r = a ^ b
    elif op == OP_NOR:
        r = 0xFF - (a | b)
    elif op == OP_SLL:
        r = (a * 2 ** (b % 8)) % 256
    else:
        r = a // 2 ** (b % 8)
    return r, int(r == 0), c, v


class TestALU(unittest.TestCase):
    def test_exhaustive(self):
        """All 8 ops x 256 x 256 = 524,288 cases."""
        for op in range(8):
            for a in range(256):
                for b in range(256):
                    got = ALU.compute(a, b, op)
                    if got != reference(a, b, op):
                        self.fail(f"op {op} a={a:02X} b={b:02X}: got {got}, expected {reference(a, b, op)}")

    # (name, op, A, B, result, Z, C, V) - same rows as tb_alu.v
    TB_ALU = [
        ("ADD 12+5", OP_ADD, 0x0C, 0x05, 0x11, 0, 0, 0),
        ("ADD FF+01 wraps", OP_ADD, 0xFF, 0x01, 0x00, 1, 1, 0),
        ("ADD 7F+01 overflow", OP_ADD, 0x7F, 0x01, 0x80, 0, 0, 1),
        ("ADD 80+80 C and V", OP_ADD, 0x80, 0x80, 0x00, 1, 1, 1),
        ("ADD 0+0 zero", OP_ADD, 0x00, 0x00, 0x00, 1, 0, 0),
        ("SUB 07-05", OP_SUB, 0x07, 0x05, 0x02, 0, 0, 0),
        ("SUB 05-07 borrow", OP_SUB, 0x05, 0x07, 0xFE, 0, 1, 0),
        ("SUB 05-05 zero", OP_SUB, 0x05, 0x05, 0x00, 1, 0, 0),
        ("SUB 80-01 overflow", OP_SUB, 0x80, 0x01, 0x7F, 0, 0, 1),
        ("SUB 7F-FF overflow", OP_SUB, 0x7F, 0xFF, 0x80, 0, 1, 1),
        ("SUB 11-05 demo1", OP_SUB, 0x11, 0x05, 0x0C, 0, 0, 0),
        ("AND F0&3C", OP_AND, 0xF0, 0x3C, 0x30, 0, 0, 0),
        ("AND 0F&F0 zero", OP_AND, 0x0F, 0xF0, 0x00, 1, 0, 0),
        ("OR  F0|0F", OP_OR, 0xF0, 0x0F, 0xFF, 0, 0, 0),
        ("XOR 05^03", OP_XOR, 0x05, 0x03, 0x06, 0, 0, 0),
        ("XOR AA^AA zero", OP_XOR, 0xAA, 0xAA, 0x00, 1, 0, 0),
        ("NOR 00 gives FF", OP_NOR, 0x00, 0x00, 0xFF, 0, 0, 0),
        ("NOR F0|0F gives 00", OP_NOR, 0xF0, 0x0F, 0x00, 1, 0, 0),
        ("SLL 05<<3", OP_SLL, 0x05, 0x03, 0x28, 0, 0, 0),
        ("SLL by 0", OP_SLL, 0x81, 0x00, 0x81, 0, 0, 0),
        ("SLL by 7", OP_SLL, 0x01, 0x07, 0x80, 0, 0, 0),
        ("SLL B=0B uses 3 bits", OP_SLL, 0x01, 0x0B, 0x08, 0, 0, 0),
        ("SLL bits fall off", OP_SLL, 0x80, 0x01, 0x00, 1, 0, 0),
        ("SRL F0>>4", OP_SRL, 0xF0, 0x04, 0x0F, 0, 0, 0),
        ("SRL by 7 zeros in", OP_SRL, 0x80, 0x07, 0x01, 0, 0, 0),
        ("SRL by 0", OP_SRL, 0xA5, 0x00, 0xA5, 0, 0, 0),
    ]

    def test_tb_alu_cases(self):
        for name, op, a, b, r, z, c, v in self.TB_ALU:
            with self.subTest(name):
                self.assertEqual(ALU.compute(a, b, op), (r, z, c, v))

    def test_named_cases_from_prompt(self):
        self.assertEqual(ALU.compute(0xFF, 0x01, OP_ADD), (0x00, 1, 1, 0))
        self.assertEqual(ALU.compute(0x7F, 0x01, OP_ADD)[0], 0x80)
        self.assertEqual(ALU.compute(0x7F, 0x01, OP_ADD)[3], 1)
        self.assertEqual(ALU.compute(0x80, 0x80, OP_ADD), (0x00, 1, 1, 1))
        r, _, c, _ = ALU.compute(0x05, 0x07, OP_SUB)
        self.assertEqual((r, c), (0xFE, 1))
        r, _, _, v = ALU.compute(0x80, 0x01, OP_SUB)
        self.assertEqual((r, v), (0x7F, 1))
        r, _, c, v = ALU.compute(0x7F, 0xFF, OP_SUB)
        self.assertEqual((r, c, v), (0x80, 1, 1))
        self.assertEqual(ALU.compute(0x01, 0x0B, OP_SLL)[0], 0x08)


if __name__ == "__main__":
    unittest.main()

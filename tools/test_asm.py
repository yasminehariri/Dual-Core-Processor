#!/usr/bin/env python3
"""test_asm.py - automatic tests for asm.py (Scope v2.3, Section 16.5).
Run from the repo root:  python tools/test_asm.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asm import assemble_text, AsmError  # noqa: E402

# The 16 verified encoding vectors from Section 12 (one per hardware instruction)
VECTORS = [
    ("ADD R3, R1, R2", 0x0650), ("SUB R4, R3, R1", 0x18C8), ("AND R5, R1, R2", 0x2A50),
    ("OR R5, R1, R2", 0x3A50), ("XOR R4, R1, R2", 0x4850), ("NOR R6, R3, R4", 0x5CE0),
    ("SLL R3, R1, R2", 0x6650), ("SRL R3, R1, R2", 0x7650), ("LOAD R1, [0x20]", 0x8220),
    ("STORE R3, [0x40]", 0x9640), ("LI R1, 5", 0xA205), ("ADDI R2, R2, -1", 0xB4BF),
    ("BEQ R3, R0, -2", 0xC63E), ("BNE R1, R2, +3", 0xD283), ("JMP 0x10", 0xE010), ("HALT", 0xF000),
]


def one(src):
    words, warnings, _ = assemble_text(src)
    return words[0], warnings


class Encodings(unittest.TestCase):
    def test_all_16_vectors(self):
        for src, exp in VECTORS:
            with self.subTest(src=src):
                self.assertEqual(one(src)[0], exp)

    def test_case_and_spacing_do_not_matter(self):
        self.assertEqual(one("  add   r3 ,r1, R2   ; comment")[0], 0x0650)

    def test_brackets_optional(self):
        self.assertEqual(one("LOAD R1, 0x20")[0], 0x8220)


class Pseudo(unittest.TestCase):
    def test_nop(self):
        w, warn = one("NOP")
        self.assertEqual(w, 0x3000)
        self.assertEqual(warn, [], "NOP must not warn about writing R0")

    def test_mov_not_clr(self):
        self.assertEqual(one("MOV R2, R5")[0], 0x3568)
        self.assertEqual(one("NOT R3, R4")[0], 0x5720)
        self.assertEqual(one("CLR R6")[0], 0x4DB0)

    def test_r0_warning_for_user_code(self):
        self.assertEqual(len(one("ADD R0, R1, R2")[1]), 1)
        self.assertEqual(len(one("LI R0, 3")[1]), 1)
        self.assertEqual(one("STORE R0, [0x10]")[1], [], "STORE reads R0, it does not write it")


class Labels(unittest.TestCase):
    def test_backward_branch(self):
        words, _, _ = assemble_text("wait: LOAD R1, [0xF0]\nBEQ R1, R0, wait\nHALT")
        self.assertEqual(words[1], 0xC23E)          # offset -2

    def test_forward_branch_and_jump(self):
        words, _, _ = assemble_text("BNE R1, R2, done\nNOP\nNOP\ndone: HALT\nJMP done")
        self.assertEqual(words[0] & 0x3F, 2)        # target 3 - (0 + 1) = +2
        self.assertEqual(words[4], 0xE003)          # absolute instruction number 3

    def test_label_on_own_line(self):
        words, _, _ = assemble_text("start:\n  LI R1, 1\n  JMP start")
        self.assertEqual(words[1], 0xE000)

    def test_offset_limits(self):
        far = "x: NOP\n" + "NOP\n" * 30 + "BEQ R1, R0, x"   # offset -32: allowed
        self.assertEqual(assemble_text(far)[0][-1] & 0x3F, 0x20)
        with self.assertRaises(AsmError):
            assemble_text("x: NOP\n" + "NOP\n" * 31 + "BEQ R1, R0, x")   # -33
        self.assertEqual(one("BEQ R1, R0, 31")[0] & 0x3F, 31)
        with self.assertRaises(AsmError):
            one("BEQ R1, R0, 32")


class Errors(unittest.TestCase):
    def bad(self, src):
        with self.assertRaises(AsmError):
            assemble_text(src)

    def test_bad_register(self):
        self.bad("ADD R8, R1, R2")
        self.bad("ADD X1, R1, R2")

    def test_out_of_range(self):
        self.bad("LI R1, 256")
        self.bad("LOAD R1, [0x100]")
        self.bad("ADDI R1, R1, 32")
        self.bad("ADDI R1, R1, -33")
        self.bad("JMP 256")

    def test_undefined_and_duplicate_labels(self):
        self.bad("BEQ R1, R0, nowhere")
        self.bad("JMP nowhere")
        self.bad("a: NOP\na: NOP")

    def test_wrong_operand_count_and_unknown(self):
        self.bad("ADD R1, R2")
        self.bad("HALT R1")
        self.bad("MUL R1, R2, R3")

    def test_program_too_long(self):
        self.bad("NOP\n" * 257)


if __name__ == "__main__":
    unittest.main(verbosity=1)

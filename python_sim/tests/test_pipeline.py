"""test_pipeline.py - python_sim/pipeline.py against hand calculations.

Rules (see pipeline.py): 5 stages, full forwarding, load-use = 1 stall,
taken BEQ/BNE = 2 flushed, JMP = 1 flushed, HALT done when it leaves WB.
Hand formula:  cycles = N + 4 (fill/drain) + stalls + flushed instructions.
"""
import unittest

from python_sim.pipeline import analyse, table
from python_sim.tests import prog


class TestPipeline(unittest.TestCase):
    def test_demo1_core1(self):
        """Demo 1, Core 1 (required result).

        LOAD R1,[01]   LOAD R2,[02]   SLL R3,R1,R2   XOR R4,R1,R2
        LOAD R5,[40]   SUB R6,R5,R1   STORE R6,[41]  HALT
        N = 8, no branches.
        Load-use: LOAD R2 -> SLL (reads R2)  = 1 stall
                  LOAD R5 -> SUB (reads R5)  = 1 stall
        SUB R6 -> STORE R6: forwarded EX/MEM->EX, no stall.
        cycles = 8 + 4 + 2 + 0 = 14.  Single-cycle 8T, pipelined 14 x 0.2T = 2.8T,
        speedup 8 / 2.8 = 2.857.
        """
        s, single = analyse(prog("demo1_core1.asm"), prog("data1.hex"))
        self.assertEqual(s.n_instr, 8)
        self.assertEqual(single, 8)
        self.assertEqual(s.cycles, 14)
        self.assertEqual(s.load_use, ["LOAD R2, [0x02] -> SLL R3, R1, R2",
                                      "LOAD R5, [0x40] -> SUB R6, R5, R1"])
        self.assertEqual((s.branch_flushes, s.jump_flushes), (0, 0))
        self.assertIn("SUB R6, R5, R1 -> STORE R6, [0x41] (EX/MEM->EX, R6)", s.forwards)
        self.assertAlmostEqual(s.cycles * 0.2, 2.8)
        self.assertAlmostEqual(s.speedup, 8 / 2.8)
        self.assertEqual(round(s.speedup, 2), 2.86)
        # diagram: SLL row = IF ID -- EX MEM WB from cycle 3
        sll = table(s)[3]
        self.assertEqual(sll[2], "SLL R3, R1, R2")
        self.assertEqual(sll[3 + 2:3 + 8], ["IF", "ID", "--", "EX", "MEM", "WB"])

    def test_demo2_core1(self):
        """Demo 2, Core 1 next to Core 0 (it spins until Core 0 sets the flag).

        Single-cycle run: the flag is read at cycles 0, 2, 4, 6, so the loop
        LOAD R1,[F0] / BEQ R1,R0,wait executes 4 times (3 taken, 1 not taken),
        then LOAD R2  LI R3  SUB R4  STORE R4  HALT.
        N = 4 x 2 + 5 = 13 (= the 13 single-cycle cycles).
        Load-use: every LOAD R1 -> BEQ R1        = 4 stalls
                  LOAD R2 -> (LI) -> SUB R2: 2 apart, MEM/WB forwarding, no stall
        Flushes:  3 taken BEQ x 2               = 6
        cycles = 13 + 4 + 4 + 6 = 27.  Speedup 13 / (27 x 0.2) = 13 / 5.4 = 2.41.
        """
        s, single = analyse(prog("demo2_core1.asm"), prog("data2.hex"), core=1,
                            other_path=prog("demo2_core0.asm"))
        self.assertEqual((s.n_instr, single), (13, 13))
        self.assertEqual(s.stall_cycles, 4)
        self.assertEqual(s.branch_flushes, 3)
        self.assertEqual(s.flushed_instructions, 6)
        self.assertEqual(s.cycles, 27)
        self.assertEqual(sum(r.flushed for r in s.rows), 6, "6 flushed rows in the diagram")
        self.assertEqual(round(s.speedup, 2), 2.41)

    def test_demo2_core1_alone_never_halts(self):
        """Without Core 0 the flag is never set: the tool must say so, not hang."""
        with self.assertRaises(RuntimeError):
            analyse(prog("demo2_core1.asm"), prog("data2.hex"), core=1)

    def test_loop_test(self):
        """loop_test: LI R1,5  CLR R2  loop: ADD R2,R2,R1  ADDI R1,R1,-1  BNE R1,R0,loop  STORE  HALT.

        N = 2 + 5 x 3 + 2 = 19 (= the 19 single-cycle cycles).
        No LOADs -> 0 stalls (ADDI R1 -> BNE R1 is forwarded EX/MEM->EX).
        BNE taken 4 times (R1 = 4, 3, 2, 1), not taken once -> 4 x 2 = 8 flushed.
        cycles = 19 + 4 + 0 + 8 = 31.  CPI 31/19 = 1.63, speedup 19 / 6.2 = 3.06.
        """
        s, single = analyse(prog("loop_test.asm"), prog("data2.hex"))
        self.assertEqual((s.n_instr, single), (19, 19))
        self.assertEqual(s.stall_cycles, 0)
        self.assertEqual(s.branch_flushes, 4)
        self.assertEqual(s.cycles, 31)
        self.assertIn("ADDI R1, R1, -1 -> BNE R1, R0, -3 (EX/MEM->EX, R1)", s.forwards)
        self.assertEqual(round(s.speedup, 2), 3.06)

    def test_core_all_with_jmp(self):
        """core_all (43 instructions, the only program with a JMP).

        Load-use: LOAD R6,[20] -> ADDI R6,R6,-1          = 1 stall
        Taken branches: BEQ R4,R0,skip1 + BNE loop x 2   = 3 x 2 = 6 flushed
        (BNE R4,R0,bad and BEQ R1,R2,bad are not taken)
        JMP done                                         = 1 flushed (the LI R5, 0xBA behind it)
        cycles = 43 + 4 + 1 + 6 + 1 = 55.
        """
        s, single = analyse(prog("core_all.asm"), prog("data2.hex"))
        self.assertEqual((s.n_instr, single), (43, 43))
        self.assertEqual(s.stall_cycles, 1)
        self.assertEqual((s.branch_flushes, s.jump_flushes), (3, 1))
        self.assertEqual(s.cycles, 55)
        jmp_flushed = [r for r in s.rows if r.flushed and r.text == "LI R5, 0xBA"]
        self.assertEqual(len(jmp_flushed), 1)


if __name__ == "__main__":
    unittest.main()

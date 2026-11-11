"""test_dual_core.py - mirrors tb/tb_dual_core.v (25 checks): Demos 1-3, single core, conflict."""
import os
import re
import unittest

from python_sim.dual_core import DualCoreSystem
from python_sim.instr_mem import InstructionMemory
from python_sim.shared_mem import SharedMemory
from python_sim.tests import REPO, prog


def run(p0: str, p1: str, data: str, on_cycle=None) -> DualCoreSystem:
    s = DualCoreSystem.from_files(prog(p0), prog(p1), prog(data))
    assert s.run(1000, on_cycle), "timeout"
    return s


class TestDualCore(unittest.TestCase):
    def test_demo1(self):
        s = run("demo1_core0.hex", "demo1_core1.hex", "data1.hex")
        r0, r1 = s.core0.dbg_regs(), s.core1.dbg_regs()
        self.assertEqual(r0[1:4], [0x0C, 0x05, 0x11])
        self.assertEqual(r1[1:7], [0x05, 0x03, 0x28, 0x06, 0x11, 0x0C])
        self.assertEqual((s.mem.mem[0x40], s.mem.mem[0x41]), (0x11, 0x0C))
        self.assertEqual((s.core0.cycle_count, s.core1.cycle_count), (5, 8))

    def test_demo2(self):
        flag_reads = []                                   # cycles where core 1 executes LOAD R1, [0xF0]

        def watch(rec):
            w = rec.wires[1]
            if w is not None and w.pc == 0:
                flag_reads.append((rec.cycle, w.mem_rdata))

        s = run("demo2_core0.hex", "demo2_core1.hex", "data2.hex", watch)
        self.assertEqual(s.mem.mem[0x80], 0x2A)
        self.assertEqual(s.mem.mem[0xF0], 0x01)
        self.assertEqual(s.mem.mem[0x81], 0x28)
        self.assertEqual((s.core0.cycle_count, s.core1.cycle_count), (7, 13))
        # core 1 reads the flag at cycles 0, 2, 4, 6 and first sees it set at cycle 6
        self.assertEqual(flag_reads, [(0, 0), (2, 0), (4, 0), (6, 1)])

    def test_demo2_trace_matches_questa(self):
        """Compare with the 'TRACE demo2 core1' lines in logs/tb_dual_core.log."""
        path = os.path.join(REPO, "logs", "tb_dual_core.log")
        if not os.path.exists(path):
            self.skipTest("logs/tb_dual_core.log not found - run Questa to enable this check")
        pat = re.compile(r"TRACE demo2 core1\s+cycle (\d+)\s+pc (\d+)\s+flag Mem\[F0\] = ([0-9a-fA-F]{2})")
        with open(path, encoding="utf-8", errors="replace") as f:
            expected = [(int(m[1]), int(m[2]), int(m[3], 16)) for m in map(pat.search, f) if m]
        got = []
        s = DualCoreSystem.from_files(prog("demo2_core0.hex"), prog("demo2_core1.hex"), prog("data2.hex"))
        while not s.both_halted:
            c1 = s.core1
            if not c1.halted:      # the testbench samples just before the edge
                got.append((c1.cycle_count, c1.pc, s.mem.read(0xF0)))
            s.clock()
        self.assertEqual(got, expected)

    def test_demo3_and_speedup(self):
        d = run("demo3_core0.hex", "demo3_core1.hex", "data3.hex")
        self.assertEqual((d.mem.mem[0x80], d.mem.mem[0x82]), (0x24, 0x88))
        self.assertEqual((d.core0.cycle_count, d.core1.cycle_count), (19, 25))
        single = run("demo3_single.hex", "halt.hex", "data3.hex")
        self.assertEqual(single.mem.mem[0x82], 0x88)
        self.assertEqual(single.core0.cycle_count, 33)
        self.assertEqual(d.dual_core_time(), 25)
        self.assertAlmostEqual(single.core0.cycle_count / d.dual_core_time(), 1.32)

    def test_conflict(self):
        s = run("conflict_core0.hex", "conflict_core1.hex", "data2.hex")
        self.assertEqual(s.mem.mem[0x50], 0xAA, "Core 0 wins")

    def test_same_cycle_read_sees_old_value(self):
        """Core 1 LOADs 0x50 in the same cycle Core 0 STOREs it: old value (00).
        One cycle later Core 1 sees the new value (AA)."""
        core0 = [0xA2AA,   # LI    R1, 0xAA
                 0x9250,   # STORE R1, [0x50]   cycle 1
                 0xF000]   # HALT
        core1 = [0x3000,   # NOP
                 0x8450,   # LOAD  R2, [0x50]   cycle 1 -> old value
                 0x8650,   # LOAD  R3, [0x50]   cycle 2 -> new value
                 0xF000]   # HALT
        s = DualCoreSystem(InstructionMemory(words=core0), InstructionMemory(words=core1), SharedMemory())
        self.assertTrue(s.run(100))
        self.assertEqual(s.core1.dbg_regs()[2], 0x00, "same-cycle read returns OLD value")
        self.assertEqual(s.core1.dbg_regs()[3], 0xAA, "next-cycle read returns NEW value")


if __name__ == "__main__":
    unittest.main()

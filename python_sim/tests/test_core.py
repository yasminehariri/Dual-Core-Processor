"""test_core.py - mirrors tb/tb_core.v (24 checks).

Like the testbench, each core gets its own data memory (a SharedMemory with
port 1 unused), loaded from data2.hex.
"""
import os
import re
import unittest

from python_sim.core import Core
from python_sim.instr_mem import InstructionMemory
from python_sim.shared_mem import SharedMemory
from python_sim.tests import REPO, prog


class SingleCore:
    """Same wiring as tb_core.v: core -> port 0 of a private shared_mem."""

    def __init__(self, prog_hex: str, data_hex: str) -> None:
        self.core = Core(InstructionMemory(prog_hex))
        self.mem = SharedMemory(data_hex)
        self.trace: list[tuple[int, int, int]] = []       # (cycle, pc, instr), like tb_core's TRACE

    def clock(self) -> None:
        c = self.core
        w = c.evaluate(self.mem.read(c.mem_addr))         # phase 1
        if not c.halted:
            self.trace.append((c.cycle_count, c.pc, w.instr))
        self.mem.clock(w.mem_addr, w.mem_wdata, w.mem_we, 0, 0, 0)   # phase 2
        c.clock(w)

    def run(self, max_cycles: int = 10_000) -> None:
        self.core.reset(); self.core.reset()              # tb holds rst for 2 edges
        for _ in range(max_cycles):
            if self.core.halted:
                return
            self.clock()
        raise AssertionError("timeout")


def verilog_trace(log_name: str) -> list[tuple[int, int, int]] | None:
    """TRACE lines from a Questa log, or None if the log is not there."""
    path = os.path.join(REPO, "logs", log_name)
    if not os.path.exists(path):
        return None
    pat = re.compile(r"TRACE\s+cycle (\d+)\s+pc (\d+)\s+instr ([0-9a-fA-F]{4})")
    with open(path, encoding="utf-8", errors="replace") as f:
        return [(int(m[1]), int(m[2]), int(m[3], 16)) for m in map(pat.search, f) if m]


class TestCore(unittest.TestCase):
    def test_core_all(self):
        s = SingleCore(prog("core_all.hex"), prog("data2.hex"))
        s.run()
        r = s.core.dbg_regs()
        self.assertEqual(r[1], 0x00, "R1 loop counter ends at 0")
        self.assertEqual(r[2], 0x06, "R2 loop sum = 6")
        self.assertEqual(r[3], 0x02, "R3 = 2 (LI)")
        self.assertEqual(r[4], 0x00, "R4 = 0 (CLR)")
        self.assertEqual(r[5], 0x77, "R5 = 77 (branch skipped EE)")
        self.assertEqual(r[6], 0x2F, "R6 = 2F (LOAD + 2 ADDI)")
        self.assertEqual(r[7], 0xD0, "R7 = D0 (MOV + NOT)")
        self.assertEqual(r[0], 0x00, "R0 never written")
        self.assertEqual(s.mem.mem[0x20:0x28], [0x11, 0xF2, 0x14, 0x03, 0x2F, 0xD0, 0x77, 0x06])
        self.assertEqual(s.core.cycle_count, 43)
        self.assertEqual(s.core.instr_count, s.core.cycle_count)
        self.assertEqual(s.core.pc, 39, "PC holds on HALT")
        for _ in range(3):
            s.clock()
        self.assertEqual(s.core.pc, 39, "PC still 39 after 3 cycles")
        self.assertEqual(s.core.cycle_count, 43, "counters stopped")
        self.assertEqual(s.core.dbg_regs(), r, "nothing written after HALT")

        vt = verilog_trace("tb_core.log")
        if vt is None:
            self.skipTest("logs/tb_core.log not found - run Questa to enable the trace comparison")
        self.assertEqual(s.trace, vt, "cycle-by-cycle trace identical to Questa")

    def test_loop_test(self):
        s = SingleCore(prog("loop_test.hex"), prog("data2.hex"))
        s.run()
        self.assertEqual(s.mem.mem[0x90], 0x0F, "Mem[90] = 5+4+3+2+1")
        self.assertEqual(s.core.dbg_regs()[2], 0x0F, "R2 = 0F")
        self.assertEqual(s.core.cycle_count, 19)


if __name__ == "__main__":
    unittest.main()

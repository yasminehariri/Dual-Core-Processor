"""Top level: two cores sharing one dual-port memory - Python model of src/dual_core_top.v.

One common clock. Each clock() is one cycle in two phases:
    Phase 1 (combinational): both cores read memory and compute all their wires
             from the CURRENT state. Nothing changes yet, so a core can never see
             a value the other core writes in the same cycle.
    Phase 2 (posedge clk):   all writes commit together - shared memory (Core 1
             first, then Core 0, so Core 0 wins a conflict), then each core's
             registers, PC and counters.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .core import Core, CoreWires
from .instr_mem import InstructionMemory
from .shared_mem import SharedMemory


@dataclass(frozen=True)
class CycleRecord:
    """What happened in one cycle, for --trace. `wires[i]` is None if core i was already halted."""
    cycle: int
    wires: tuple[Optional[CoreWires], Optional[CoreWires]]


class DualCoreSystem:
    """dual_core_top.v. imem0/imem1/mem play the roles of PROG0, PROG1 and DATA."""

    def __init__(self, imem0: InstructionMemory, imem1: InstructionMemory, mem: SharedMemory) -> None:
        self.core0 = Core(imem0)
        self.core1 = Core(imem1)
        self.mem = mem
        self.cycle: int = 0          # global clock cycles since reset was released
        self.reset()

    @classmethod
    def from_files(cls, prog0: str, prog1: str, data: str) -> "DualCoreSystem":
        return cls(InstructionMemory(prog0), InstructionMemory(prog1), SharedMemory(data))

    @property
    def cores(self) -> tuple[Core, Core]:
        return self.core0, self.core1

    @property
    def both_halted(self) -> bool:
        return bool(self.core0.halted and self.core1.halted)

    def reset(self) -> None:
        """Hold rst for two edges, like the testbenches (memory is not reset, as in shared_mem.v)."""
        for _ in range(2):
            for c in self.cores:
                c.reset()
        self.cycle = 0

    def clock(self) -> CycleRecord:
        """Advance one clock cycle."""
        c0, c1 = self.cores
        # ---- phase 1: combinational, from the current state ----
        w0 = c0.evaluate(self.mem.read(c0.mem_addr))     # rdata0 = mem[addr0]
        w1 = c1.evaluate(self.mem.read(c1.mem_addr))     # rdata1 = mem[addr1]
        record = CycleRecord(self.cycle, (None if c0.halted else w0, None if c1.halted else w1))
        # ---- phase 2: posedge clk, everything commits together ----
        self.mem.clock(w0.mem_addr, w0.mem_wdata, w0.mem_we,
                       w1.mem_addr, w1.mem_wdata, w1.mem_we)
        c0.clock(w0)
        c1.clock(w1)
        self.cycle += 1
        return record

    def run(self, max_cycles: int = 1000, on_cycle=None) -> bool:
        """Clock until both cores halt. Returns True if they did within max_cycles.
        `on_cycle(record)` is called after every cycle (used by --trace)."""
        while not self.both_halted:
            if self.cycle >= max_cycles:
                return False
            rec = self.clock()
            if on_cycle is not None:
                on_cycle(rec)
        return True

    def dual_core_time(self) -> int:
        """T_dual = max(C0, C1) - the cores run in parallel, so never the sum."""
        return max(self.core0.cycle_count, self.core1.cycle_count)

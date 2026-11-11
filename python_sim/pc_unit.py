"""8-bit program counter - Python model of src/pc_unit.v.

Next-PC priority (one if/else chain, exactly like the Verilog):
    reset > (halt or already halted: hold PC, set halted) > jump > branch taken > PC + 1
"""
from __future__ import annotations

from .decoder import sext6


class PCUnit:
    """pc_unit.v: registers `pc` and `halted`."""

    def __init__(self) -> None:
        self.pc: int = 0
        self.halted: int = 0

    def branch_target(self, off6: int) -> int:
        """PC + 1 + sign-extend(off6), 8-bit wrap."""
        return (self.pc + 1 + sext6(off6)) & 0xFF

    def next_state(self, rst: int, halt: int, jump: int, branch_taken: int,
                   jump_addr: int, off6: int) -> tuple[int, int]:
        """Combinational: the (pc, halted) the next clock edge will load."""
        if rst:
            return 0x00, 0
        if halt or self.halted:
            return self.pc, 1                      # stay on the HALT instruction
        if jump:
            return jump_addr & 0xFF, self.halted
        if branch_taken:
            return self.branch_target(off6), self.halted
        return (self.pc + 1) & 0xFF, self.halted

    def clock(self, rst: int, halt: int, jump: int, branch_taken: int,
              jump_addr: int, off6: int) -> None:
        """One posedge clk."""
        self.pc, self.halted = self.next_state(rst, halt, jump, branch_taken, jump_addr, off6)

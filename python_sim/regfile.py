"""8 x 8-bit register file - Python model of src/regfile.v.

Two combinational read ports and one write port that updates only at the
clock edge, so a value written in cycle n is readable from cycle n+1.
"""
from __future__ import annotations


class RegisterFile:
    """regfile.v: regs[0..7], synchronous active-high reset."""

    def __init__(self) -> None:
        self.regs: list[int] = [0] * 8   # Python starts in the post-reset state (Verilog starts at X)

    def reset(self) -> None:
        """Clock edge with rst = 1: clear R0..R7."""
        self.regs = [0] * 8

    def read(self, ra: int) -> int:
        """Combinational read port (rd1 = regs[ra1], rd2 = regs[ra2])."""
        return self.regs[ra & 0b111]

    def write(self, wa: int, wd: int, we: int) -> None:
        """Clock edge with rst = 0: if we, regs[wa] <= wd.

        Call this only in the commit phase of a cycle, after every read of the cycle.
        """
        if we:
            self.regs[wa & 0b111] = wd & 0xFF

    def dbg(self) -> list[int]:
        """dbg_r0..dbg_r7 as a list [R0, R1, ..., R7]."""
        return list(self.regs)

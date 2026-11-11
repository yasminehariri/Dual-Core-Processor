"""256 x 8 dual-port shared data memory - Python model of src/shared_mem.v.

- Cleared to 0x00, then loaded from the data file ($readmemh fills only the listed bytes).
- Combinational reads: a read in the same cycle as a write sees the OLD value.
- Both ports write at the same edge; Core 1's write is applied first, then
  Core 0's, so on a same-address conflict Core 0's value wins.
"""
from __future__ import annotations

from typing import Optional

from .hexfile import read_memh

SIZE = 256


class SharedMemory:
    """shared_mem.v: port 0 = Core 0, port 1 = Core 1."""

    def __init__(self, hex_path: Optional[str] = None) -> None:
        self.mem: list[int] = [0x00] * SIZE
        if hex_path is not None:
            read_memh(hex_path, self.mem, 0xFF)

    def read(self, addr: int) -> int:
        """rdata0 = mem[addr0] / rdata1 = mem[addr1] (both ports read the same way)."""
        return self.mem[addr & 0xFF]

    def clock(self, addr0: int, wdata0: int, we0: int,
              addr1: int, wdata1: int, we1: int) -> None:
        """One posedge clk. Order matters: port 1 first, port 0 last -> Core 0 wins."""
        if we1:
            self.mem[addr1 & 0xFF] = wdata1 & 0xFF
        if we0:
            self.mem[addr0 & 0xFF] = wdata0 & 0xFF

    def nonzero(self) -> dict[int, int]:
        """{address: value} for every non-zero byte."""
        return {a: v for a, v in enumerate(self.mem) if v}

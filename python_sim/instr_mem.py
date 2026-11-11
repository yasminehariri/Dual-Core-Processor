"""256 x 16 instruction ROM - Python model of src/instr_mem.v.

Every word is first set to HALT (0xF000), then the program is loaded with
$readmemh semantics, so a core that runs off its program stops safely.
"""
from __future__ import annotations

from typing import Iterable, Optional

from .hexfile import read_memh

HALT_WORD = 0xF000
SIZE = 256


class InstructionMemory:
    """instr_mem.v: combinational read, no write port."""

    def __init__(self, hex_path: Optional[str] = None, words: Optional[Iterable[int]] = None) -> None:
        """Load from a .hex file (like the PROG parameter) or from a list of words
        (used when run.py assembles a .asm file directly)."""
        self.mem: list[int] = [HALT_WORD] * SIZE
        if hex_path is not None:
            read_memh(hex_path, self.mem, 0xFFFF)
        if words is not None:
            for i, w in enumerate(words):
                self.mem[i] = w & 0xFFFF

    def read(self, addr: int) -> int:
        """instr = mem[addr]."""
        return self.mem[addr & 0xFF]

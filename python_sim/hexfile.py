"""Reader for the hex files the Verilog loads with $readmemh.

Mirrors what $readmemh does with our files: whitespace-separated hex words,
'//' line comments, '/* */' block comments, and optional '@addr' jumps.
Only the listed words are filled; the caller pre-fills the rest
(0xF000 in instr_mem.v, 0x00 in shared_mem.v).
"""
from __future__ import annotations

import re


def read_memh(path: str, mem: list[int], width_mask: int) -> None:
    """Load `path` into `mem` in place, exactly like `$readmemh(path, mem)`.

    Each word is masked to `width_mask` (0xFFFF for instructions, 0xFF for data).
    Raises ValueError if a token is not hex or the file overruns the memory.
    """
    with open(path, encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)   # block comments
    text = re.sub(r"//[^\n]*", " ", text)                 # line comments
    addr = 0
    for tok in text.split():
        tok = tok.replace("_", "")                        # Verilog allows 12_34
        if tok.startswith("@"):
            addr = int(tok[1:], 16)
            continue
        if addr >= len(mem):
            raise ValueError(f"{path}: data runs past address {len(mem) - 1}")
        mem[addr] = int(tok, 16) & width_mask
        addr += 1

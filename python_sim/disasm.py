"""Disassembler for trace output (no Verilog counterpart; inverse of tools/asm.py)."""
from __future__ import annotations

from .decoder import decode

MNEMONICS = ["ADD", "SUB", "AND", "OR", "XOR", "NOR", "SLL", "SRL",
             "LOAD", "STORE", "LI", "ADDI", "BEQ", "BNE", "JMP", "HALT"]


def _s6(x: int) -> int:
    return x - 64 if x & 0x20 else x


def disassemble(instr: int, pc: int | None = None) -> str:
    """One instruction as assembly text. With `pc`, branches also show the target."""
    f = decode(instr)
    m = MNEMONICS[f.opcode]
    if f.opcode <= 7:
        return f"{m} R{f.rd}, R{f.rs}, R{f.rt}"
    if m in ("LOAD", "STORE"):
        return f"{m} R{f.rd}, [0x{f.addr8:02X}]"
    if m == "LI":
        return f"LI R{f.rd}, 0x{f.addr8:02X}"
    if m == "ADDI":
        return f"ADDI R{f.rd}, R{f.rs}, {_s6(f.off6)}"
    if m in ("BEQ", "BNE"):
        text = f"{m} R{f.rd}, R{f.rs}, {_s6(f.off6):+d}"
        if pc is not None:
            text += f"  (-> {(pc + 1 + _s6(f.off6)) & 0xFF})"
        return text
    if m == "JMP":
        return f"JMP {f.addr8}"
    return "HALT"

"""Instruction decoder - Python model of src/decoder.v.

Every format uses the same bit positions, so decoding is pure wiring:
    opcode [15:12]  rd [11:9]  rs [8:6]  rt [5:3]  imm6/off6 [5:0]  addr8 [7:0]
"""
from __future__ import annotations

from typing import NamedTuple


class Fields(NamedTuple):
    """Output ports of decoder.v."""
    opcode: int      # instr[15:12]
    rd: int          # instr[11:9]  destination (or STORE source / branch Ra)
    rs: int          # instr[8:6]   read port 1 (or branch Rb)
    rt: int          # instr[5:3]   read port 2 for R-type
    imm6_sext: int   # instr[5:0] sign-extended to 8 bits (ADDI)
    off6: int        # instr[5:0] raw 6 bits; pc_unit sign-extends it (as in decoder.v)
    addr8: int       # instr[7:0]   LOAD/STORE address, LI imm8, JMP target


def sext6(x: int) -> int:
    """Sign-extend 6 bits to 8: {{2{x[5]}}, x[5:0]}."""
    x &= 0x3F
    return (x | 0xC0) if x & 0x20 else x


def decode(instr: int) -> Fields:
    """Split a 16-bit instruction into its fields."""
    instr &= 0xFFFF
    return Fields(
        opcode=(instr >> 12) & 0xF,
        rd=(instr >> 9) & 0b111,
        rs=(instr >> 6) & 0b111,
        rt=(instr >> 3) & 0b111,
        imm6_sext=sext6(instr),
        off6=instr & 0x3F,
        addr8=instr & 0xFF,
    )

"""Control unit - Python model of src/control_unit.v.

Opcode -> 11 control signals (14 bits). Defaults are all 0, exactly like the
Verilog `always @(*)` block, then each opcode turns on what it needs.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Control:
    """Output ports of control_unit.v."""
    reg_write: int = 0
    alu_src: int = 0     # 0: ReadData2   1: sign-extended imm6
    alu_op: int = 0      # 3 bits
    mem_read: int = 0
    mem_write: int = 0
    wb_sel: int = 0      # 2 bits: 00 ALU, 01 memory, 10 imm8
    reg2_sel: int = 0    # 0: inst[5:3]   1: inst[11:9]
    branch: int = 0
    br_ne: int = 0
    jump: int = 0
    halt: int = 0

    def bits(self) -> int:
        """All 14 bits packed in table order, like `ctl` in tb_control_unit.v:
        RegWr ALUSrc ALUOp[2:0] MemRd MemWr WBSel[1:0] Reg2Sel Branch BrNE Jump Halt."""
        v = 0
        for value, width in ((self.reg_write, 1), (self.alu_src, 1), (self.alu_op, 3), (self.mem_read, 1),
                             (self.mem_write, 1), (self.wb_sel, 2), (self.reg2_sel, 1), (self.branch, 1),
                             (self.br_ne, 1), (self.jump, 1), (self.halt, 1)):
            v = (v << width) | (value & ((1 << width) - 1))
        return v


def control(opcode: int) -> Control:
    """Decode a 4-bit opcode into control signals (case statement of control_unit.v)."""
    opcode &= 0xF
    if opcode <= 0b0111:                                   # R-type: ADD..SRL
        return Control(reg_write=1, alu_op=opcode & 0b111)
    if opcode == 0b1000:                                   # LOAD
        return Control(reg_write=1, mem_read=1, wb_sel=0b01)
    if opcode == 0b1001:                                   # STORE
        return Control(mem_write=1, reg2_sel=1)
    if opcode == 0b1010:                                   # LI
        return Control(reg_write=1, wb_sel=0b10)
    if opcode == 0b1011:                                   # ADDI (alu_op = ADD)
        return Control(reg_write=1, alu_src=1)
    if opcode == 0b1100:                                   # BEQ (compare with SUB)
        return Control(alu_op=0b001, reg2_sel=1, branch=1)
    if opcode == 0b1101:                                   # BNE
        return Control(alu_op=0b001, reg2_sel=1, branch=1, br_ne=1)
    if opcode == 0b1110:                                   # JMP
        return Control(jump=1)
    return Control(halt=1)                                 # 0b1111 HALT

"""8-bit ALU - Python model of src/alu.v.

Operations (alu_op = opcode[2:0]): ADD SUB AND OR XOR NOR SLL SRL.
Flags: zero for every op; carry and overflow for ADD and SUB only (0 otherwise).
"""
from __future__ import annotations

OP_ADD, OP_SUB, OP_AND, OP_OR, OP_XOR, OP_NOR, OP_SLL, OP_SRL = range(8)
OP_NAMES = ["ADD", "SUB", "AND", "OR", "XOR", "NOR", "SLL", "SRL"]


class ALU:
    """Combinational ALU (alu.v). No state, so compute() is a static method."""

    @staticmethod
    def compute(a: int, b: int, alu_op: int) -> tuple[int, int, int, int]:
        """Return (result, zero, carry, overflow) for 8-bit inputs a, b.

        Like alu.v, ADD and SUB share ONE 9-bit adder:
            sum = a + b_in + cin
            ADD: b_in = b,  cin = 0, carry = sum[8]
            SUB: b_in = ~b, cin = 1, carry = ~sum[8]  (borrow: 1 when a < b unsigned)
        """
        a &= 0xFF
        b &= 0xFF
        alu_op &= 0b111

        is_sub = 1 if alu_op == OP_SUB else 0
        b_in = (~b & 0xFF) if is_sub else b
        total = a + b_in + is_sub                     # 9-bit sum, bit 8 = carry out

        a7, b7 = a >> 7, b >> 7
        carry = overflow = 0
        if alu_op == OP_ADD:
            result = total & 0xFF
            carry = (total >> 8) & 1
            overflow = int(a7 == b7 and (result >> 7) != a7)    # pos+pos=neg or neg+neg=pos
        elif alu_op == OP_SUB:
            result = total & 0xFF
            carry = 1 - ((total >> 8) & 1)                       # borrow
            overflow = int(a7 != b7 and (result >> 7) != a7)    # pos-neg=neg or neg-pos=pos
        elif alu_op == OP_AND:
            result = a & b
        elif alu_op == OP_OR:
            result = a | b
        elif alu_op == OP_XOR:
            result = a ^ b
        elif alu_op == OP_NOR:
            result = ~(a | b) & 0xFF
        elif alu_op == OP_SLL:
            result = (a << (b & 0b111)) & 0xFF                   # b[2:0] only, zeros in
        else:  # OP_SRL
            result = a >> (b & 0b111)                            # logical shift, zeros in

        zero = int(result == 0)
        return result, zero, carry, overflow

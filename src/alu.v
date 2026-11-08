// ============================================================================
// CCEE 324 Dual-Core Processor  |  alu.v
// Purpose : 8-bit ALU: ADD SUB AND OR XOR NOR SLL SRL + Zero/Carry/Overflow
// Spec    : Scope document v2.3, Section 13.3
// Author  : Yasmine (RTL lead)
// Status  : STUB - ports are final, logic still to be written
// ============================================================================
`timescale 1ns/1ps
`default_nettype none
module alu (
    input  wire [7:0] a,         // operand A = register Rs (read port 1)
    input  wire [7:0] b,         // operand B = register Rt, or sign-extended imm6
    input  wire [2:0] alu_op,    // operation select = opcode[2:0]
    output wire [7:0] result,
    output wire       zero,      // 1 when result == 8'h00
    output wire       carry,     // ADD: sum[8]; SUB: borrow = ~sum[8]
    output wire       overflow   // signed overflow for ADD and SUB
);
    // TODO (Yasmine): replace with the real ALU from Section 13.3
    assign result   = 8'h00;
    assign zero     = 1'b0;
    assign carry    = 1'b0;
    assign overflow = 1'b0;
endmodule
`default_nettype wire

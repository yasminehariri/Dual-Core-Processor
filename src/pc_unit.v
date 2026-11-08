// ============================================================================
// CCEE 324 Dual-Core Processor  |  pc_unit.v
// Purpose : 8-bit program counter with jump, branch and halt
// Spec    : Scope document v2.3, Section 13.2 (next-PC priority)
// Author  : Yasmine (RTL lead)
// Status  : STUB - ports are final, logic still to be written
// ============================================================================
`timescale 1ns/1ps
`default_nettype none
module pc_unit (
    input  wire       clk,
    input  wire       rst,
    input  wire       halt,          // current instruction is HALT
    input  wire       jump,
    input  wire       branch_taken,
    input  wire [7:0] jump_addr,     // addr8
    input  wire [5:0] off6,          // signed branch offset
    output wire [7:0] pc,
    output wire       halted
);
    // TODO (Yasmine): branch_target = pc + 8'd1 + {{2{off6[5]}}, off6};
    assign pc = 8'h00;
    assign halted = 1'b0;
endmodule
`default_nettype wire

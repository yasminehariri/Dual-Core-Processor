// ============================================================================
// CCEE 324 Dual-Core Processor  |  regfile.v
// Purpose : 8 x 8-bit register file, 2 combinational reads, 1 write on posedge
// Spec    : Scope document v2.3, Section 13.4
// Author  : Yasmine (RTL lead)
// Status  : STUB - ports are final, logic still to be written
// ============================================================================
`timescale 1ns/1ps
`default_nettype none
module regfile (
    input  wire       clk,
    input  wire       rst,       // synchronous, active high: clears R0..R7
    input  wire [2:0] ra1,       // read address 1 (Rs = inst[8:6])
    input  wire [2:0] ra2,       // read address 2 (Rt, or inst[11:9] for STORE/BEQ/BNE)
    input  wire [2:0] wa,        // write address (Rd = inst[11:9])
    input  wire [7:0] wd,        // write data
    input  wire       we,        // write enable (RegWrite)
    output wire [7:0] rd1,
    output wire [7:0] rd2,
    output wire [7:0] dbg_r0, dbg_r1, dbg_r2, dbg_r3,
    output wire [7:0] dbg_r4, dbg_r5, dbg_r6, dbg_r7
);
    // TODO (Yasmine): reg [7:0] regs [0:7]; combinational reads; write on posedge when we
    assign rd1 = 8'h00;  assign rd2 = 8'h00;
    assign dbg_r0 = 8'h00; assign dbg_r1 = 8'h00; assign dbg_r2 = 8'h00; assign dbg_r3 = 8'h00;
    assign dbg_r4 = 8'h00; assign dbg_r5 = 8'h00; assign dbg_r6 = 8'h00; assign dbg_r7 = 8'h00;
endmodule
`default_nettype wire

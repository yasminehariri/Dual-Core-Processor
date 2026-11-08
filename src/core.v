// ============================================================================
// CCEE 324 Dual-Core Processor  |  core.v
// Purpose : One CPU core: decoder, control unit, PC, instruction memory, register file, ALU
// Spec    : Scope document v2.3, Sections 13.2 and 15
// Author  : Yasmine (RTL lead)
// Status  : STUB - ports are final, logic still to be written
// ============================================================================
`timescale 1ns/1ps
`default_nettype none
module core #(
    parameter PROG      = "programs/core0.hex",
    parameter PIPELINED = 0                    // Tier B only; 0 = single-cycle
) (
    input  wire        clk,
    input  wire        rst,
    // shared memory port
    input  wire [7:0]  mem_rdata,
    output wire [7:0]  mem_addr,
    output wire [7:0]  mem_wdata,
    output wire        mem_we,
    // status and debug
    output wire        halted,
    output wire [7:0]  pc,
    output wire [15:0] cycle_count,
    output wire [15:0] instr_count,
    output wire [63:0] dbg_regs              // {R7, R6, R5, R4, R3, R2, R1, R0}
);
    // TODO (Yasmine, Phase 2): instantiate decoder, control_unit, pc_unit,
    //   instr_mem #(.PROG(PROG)), regfile, alu; add the 4 muxes and the counters
    assign mem_addr = 8'h00; assign mem_wdata = 8'h00; assign mem_we = 1'b0;
    assign halted = 1'b0; assign pc = 8'h00;
    assign cycle_count = 16'd0; assign instr_count = 16'd0; assign dbg_regs = 64'd0;
endmodule
`default_nettype wire

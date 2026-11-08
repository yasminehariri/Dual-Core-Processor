// ============================================================================
// CCEE 324 Dual-Core Processor  |  dual_core_top.v
// Purpose : Top level: two identical cores sharing one dual-port data memory
// Spec    : Scope document v2.3, Sections 13.1 and 15
// Author  : Yasmine (RTL lead)
// Status  : COMPLETE wiring (cores and memory are still stubs)
// ============================================================================
`timescale 1ns/1ps
`default_nettype none
module dual_core_top #(
    parameter PROG0     = "programs/core0.hex",
    parameter PROG1     = "programs/core1.hex",
    parameter DATA      = "programs/data.hex",
    parameter PIPELINED = 0
) (
    input  wire        clk,
    input  wire        rst,
    output wire        halted0,
    output wire        halted1,
    output wire        both_halted,
    // debug buses (visible in the Questa wave window)
    output wire [7:0]  pc0,
    output wire [7:0]  pc1,
    output wire [63:0] regs0,
    output wire [63:0] regs1,
    output wire [15:0] cycles0,
    output wire [15:0] cycles1
);
    wire [7:0] addr0, wdata0, rdata0, addr1, wdata1, rdata1;
    wire       we0, we1;
    wire [15:0] icount0, icount1;

    core #(.PROG(PROG0), .PIPELINED(PIPELINED)) core0 (
        .clk(clk), .rst(rst),
        .mem_rdata(rdata0), .mem_addr(addr0), .mem_wdata(wdata0), .mem_we(we0),
        .halted(halted0), .pc(pc0), .cycle_count(cycles0), .instr_count(icount0), .dbg_regs(regs0)
    );

    core #(.PROG(PROG1), .PIPELINED(PIPELINED)) core1 (
        .clk(clk), .rst(rst),
        .mem_rdata(rdata1), .mem_addr(addr1), .mem_wdata(wdata1), .mem_we(we1),
        .halted(halted1), .pc(pc1), .cycle_count(cycles1), .instr_count(icount1), .dbg_regs(regs1)
    );

    shared_mem #(.INIT(DATA)) mem (
        .clk(clk),
        .addr0(addr0), .wdata0(wdata0), .we0(we0), .rdata0(rdata0),
        .addr1(addr1), .wdata1(wdata1), .we1(we1), .rdata1(rdata1)
    );

    assign both_halted = halted0 & halted1;
endmodule
`default_nettype wire

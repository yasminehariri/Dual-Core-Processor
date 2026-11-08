// ============================================================================
// CCEE 324 Dual-Core Processor  |  shared_mem.v
// Purpose : 256 x 8 dual-port shared data memory, Core 0 wins write conflicts
// Spec    : Scope document v2.3, Section 13.6
// Author  : Yasmine (RTL lead)
// Status  : COMPLETE
// ============================================================================
`timescale 1ns/1ps
`default_nettype none
module shared_mem #(
    parameter INIT = "programs/data.hex"
) (
    input  wire       clk,
    // port 0 (Core 0)
    input  wire [7:0] addr0,
    input  wire [7:0] wdata0,
    input  wire       we0,
    output wire [7:0] rdata0,
    // port 1 (Core 1)
    input  wire [7:0] addr1,
    input  wire [7:0] wdata1,
    input  wire       we1,
    output wire [7:0] rdata1
);
    reg [7:0] mem [0:255];
    integer i;

    // clear all 256 bytes, then load the data file ($readmemh fills only the bytes it lists)
    initial begin
        for (i = 0; i < 256; i = i + 1) mem[i] = 8'h00;
        $readmemh(INIT, mem);
    end

    // Both ports write at the same edge. Core 1's write is applied first and
    // Core 0's second, so when both hit the same address Core 0's value wins.
    always @(posedge clk) begin
        if (we1) mem[addr1] <= wdata1;
        if (we0) mem[addr0] <= wdata0;
    end

    // combinational reads: a read in the same cycle as a write sees the old value
    assign rdata0 = mem[addr0];
    assign rdata1 = mem[addr1];
endmodule
`default_nettype wire

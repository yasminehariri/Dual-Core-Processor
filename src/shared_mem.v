// ============================================================================
// CCEE 324 Dual-Core Processor  |  shared_mem.v
// Purpose : 256 x 8 dual-port shared data memory, Core 0 wins write conflicts
// Spec    : Scope document v2.3, Section 13.6
// Author  : Yasmine (RTL lead)
// Status  : STUB - ports are final, logic still to be written
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
    // TODO (Yasmine): clear all 256 bytes, then $readmemh(INIT);
    //   one always @(posedge clk): apply Core 1's write first, then Core 0's
    assign rdata0 = 8'h00;
    assign rdata1 = 8'h00;
endmodule
`default_nettype wire

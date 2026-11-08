// ============================================================================
// CCEE 324 Dual-Core Processor  |  instr_mem.v
// Purpose : 256 x 16 instruction ROM, one per core
// Spec    : Scope document v2.3, Section 13.1
// Author  : Yasmine (RTL lead)
// Status  : STUB - ports are final, logic still to be written
// ============================================================================
`timescale 1ns/1ps
`default_nettype none
module instr_mem #(
    parameter PROG = "programs/core0.hex"   // path from the repo root (Questa) - see README
) (
    input  wire [7:0]  addr,
    output wire [15:0] instr
);
    // TODO (Yasmine): fill all 256 words with 16'hF000 (HALT), then $readmemh(PROG, mem)
    assign instr = 16'hF000;
endmodule
`default_nettype wire

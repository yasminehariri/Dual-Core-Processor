// ============================================================================
// CCEE 324 Dual-Core Processor  |  instr_mem.v
// Purpose : 256 x 16 instruction ROM, one per core
// Spec    : Scope document v2.3, Section 13.1
// Author  : Yasmine (RTL lead)
// Status  : COMPLETE
// ============================================================================
`timescale 1ns/1ps
`default_nettype none
module instr_mem #(
    parameter PROG = "programs/core0.hex"   // path from the repo root (Questa) - see README
) (
    input  wire [7:0]  addr,
    output wire [15:0] instr
);
    reg [15:0] mem [0:255];
    integer i;

    // every unused word is HALT, so a core that runs off its program stops safely
    initial begin
        for (i = 0; i < 256; i = i + 1) mem[i] = 16'hF000;
        $readmemh(PROG, mem);
    end

    assign instr = mem[addr];       // combinational read
endmodule
`default_nettype wire

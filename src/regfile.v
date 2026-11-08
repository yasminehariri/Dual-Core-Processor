// ============================================================================
// CCEE 324 Dual-Core Processor  |  regfile.v
// Purpose : 8 x 8-bit register file, 2 combinational reads, 1 write on posedge
// Spec    : Scope document v2.3, Section 13.4
// Author  : Yasmine (RTL lead)
// Status  : COMPLETE
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
    reg [7:0] regs [0:7];
    integer i;

    // write port: one register per clock edge, only when we = 1
    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 8; i = i + 1) regs[i] <= 8'h00;
        end else if (we) begin
            regs[wa] <= wd;
        end
    end

    // read ports: combinational, so a value written at edge n is read from cycle n+1
    assign rd1 = regs[ra1];
    assign rd2 = regs[ra2];

    // debug outputs, visible in the wave window
    assign dbg_r0 = regs[0]; assign dbg_r1 = regs[1]; assign dbg_r2 = regs[2]; assign dbg_r3 = regs[3];
    assign dbg_r4 = regs[4]; assign dbg_r5 = regs[5]; assign dbg_r6 = regs[6]; assign dbg_r7 = regs[7];
endmodule
`default_nettype wire

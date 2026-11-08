// ============================================================================
// CCEE 324 Dual-Core Processor  |  pc_unit.v
// Purpose : 8-bit program counter with jump, branch and halt
// Spec    : Scope document v2.3, Section 13.2 (next-PC priority)
// Author  : Yasmine (RTL lead)
// Status  : COMPLETE
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
    output reg  [7:0] pc,
    output reg        halted
);
    wire [7:0] pc_plus1      = pc + 8'd1;
    wire [7:0] branch_target = pc + 8'd1 + {{2{off6[5]}}, off6};   // PC + 1 + sign-extend(off6), 8-bit wrap

    // next-PC priority: reset > halt > jump > branch taken > PC + 1
    always @(posedge clk) begin
        if (rst) begin
            pc     <= 8'h00;
            halted <= 1'b0;
        end else if (halt || halted) begin
            pc     <= pc;            // stay on the HALT instruction
            halted <= 1'b1;
        end else if (jump) begin
            pc <= jump_addr;
        end else if (branch_taken) begin
            pc <= branch_target;
        end else begin
            pc <= pc_plus1;
        end
    end
endmodule
`default_nettype wire

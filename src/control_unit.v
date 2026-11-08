// ============================================================================
// CCEE 324 Dual-Core Processor  |  control_unit.v
// Purpose : Opcode to 11 control signals (14 bits)
// Spec    : Scope document v2.3, Section 13.5 (truth table)
// Author  : Yasmine (RTL lead)
// Status  : STUB - ports are final, logic still to be written
// ============================================================================
`timescale 1ns/1ps
`default_nettype none
module control_unit (
    input  wire [3:0] opcode,
    output wire       reg_write,
    output wire       alu_src,     // 0: ReadData2   1: sign-extended imm6
    output wire [2:0] alu_op,
    output wire       mem_read,
    output wire       mem_write,
    output wire [1:0] wb_sel,      // 00 ALU, 01 memory, 10 imm8
    output wire       reg2_sel,    // 0: inst[5:3]   1: inst[11:9]
    output wire       branch,
    output wire       br_ne,
    output wire       jump,
    output wire       halt
);
    // TODO (Yasmine): always @(*) case (opcode) from the table in Section 13.5
    assign reg_write = 1'b0; assign alu_src = 1'b0; assign alu_op = 3'd0;
    assign mem_read = 1'b0; assign mem_write = 1'b0; assign wb_sel = 2'd0;
    assign reg2_sel = 1'b0; assign branch = 1'b0; assign br_ne = 1'b0;
    assign jump = 1'b0; assign halt = 1'b0;
endmodule
`default_nettype wire

// ============================================================================
// CCEE 324 Dual-Core Processor  |  decoder.v
// Purpose : Instruction decoder: splits a 16-bit instruction into fields
// Spec    : Scope document v2.3, Sections 12 and 13.2
// Author  : Yasmine (RTL lead)
// Status  : STUB - ports are final, logic still to be written
// ============================================================================
`timescale 1ns/1ps
`default_nettype none
module decoder (
    input  wire [15:0] instr,
    output wire [3:0]  opcode,     // instr[15:12]
    output wire [2:0]  rd,         // instr[11:9]
    output wire [2:0]  rs,         // instr[8:6]
    output wire [2:0]  rt,         // instr[5:3]
    output wire [7:0]  imm6_sext,  // sign-extended instr[5:0] (ADDI)
    output wire [5:0]  off6,       // instr[5:0] (branch offset, signed)
    output wire [7:0]  addr8       // instr[7:0] (LOAD/STORE address, LI imm8, JMP target)
);
    // TODO (Yasmine): pure wiring, see Section 12
    assign opcode = 4'h0; assign rd = 3'd0; assign rs = 3'd0; assign rt = 3'd0;
    assign imm6_sext = 8'h00; assign off6 = 6'd0; assign addr8 = 8'h00;
endmodule
`default_nettype wire

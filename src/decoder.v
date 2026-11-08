// ============================================================================
// CCEE 324 Dual-Core Processor  |  decoder.v
// Purpose : Instruction decoder: splits a 16-bit instruction into fields
// Spec    : Scope document v2.3, Sections 12 and 13.2
// Author  : Yasmine (RTL lead)
// Status  : COMPLETE
// ============================================================================
`timescale 1ns/1ps
`default_nettype none
module decoder (
    input  wire [15:0] instr,
    output wire [3:0]  opcode,     // instr[15:12]
    output wire [2:0]  rd,         // instr[11:9]  destination (or STORE source / branch Ra)
    output wire [2:0]  rs,         // instr[8:6]   read port 1 (or branch Rb)
    output wire [2:0]  rt,         // instr[5:3]   read port 2 for R-type
    output wire [7:0]  imm6_sext,  // instr[5:0] sign-extended to 8 bits (ADDI)
    output wire [5:0]  off6,       // instr[5:0] signed branch offset
    output wire [7:0]  addr8       // instr[7:0] LOAD/STORE address, LI imm8, JMP target
);
    // Fixed field positions in every format, so decoding is pure wiring.
    assign opcode    = instr[15:12];
    assign rd        = instr[11:9];
    assign rs        = instr[8:6];
    assign rt        = instr[5:3];
    assign imm6_sext = {{2{instr[5]}}, instr[5:0]};   // copy the sign bit into bits 7:6
    assign off6      = instr[5:0];
    assign addr8     = instr[7:0];
endmodule
`default_nettype wire

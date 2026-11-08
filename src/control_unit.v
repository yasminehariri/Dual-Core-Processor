// ============================================================================
// CCEE 324 Dual-Core Processor  |  control_unit.v
// Purpose : Opcode to 11 control signals (14 bits)
// Spec    : Scope document v2.3, Section 13.5 (truth table)
// Author  : Yasmine (RTL lead)
// Status  : COMPLETE
// ============================================================================
`timescale 1ns/1ps
`default_nettype none
module control_unit (
    input  wire [3:0] opcode,
    output reg        reg_write,
    output reg        alu_src,     // 0: ReadData2   1: sign-extended imm6
    output reg  [2:0] alu_op,
    output reg        mem_read,
    output reg        mem_write,
    output reg  [1:0] wb_sel,      // 00 ALU, 01 memory, 10 imm8
    output reg        reg2_sel,    // 0: inst[5:3]   1: inst[11:9]
    output reg        branch,
    output reg        br_ne,
    output reg        jump,
    output reg        halt
);
    always @(*) begin
        // defaults = all signals off (don't-cares are written as 0)
        reg_write = 1'b0; alu_src = 1'b0; alu_op = 3'b000; mem_read = 1'b0; mem_write = 1'b0;
        wb_sel = 2'b00; reg2_sel = 1'b0; branch = 1'b0; br_ne = 1'b0; jump = 1'b0; halt = 1'b0;
        case (opcode)
            4'b0000, 4'b0001, 4'b0010, 4'b0011,
            4'b0100, 4'b0101, 4'b0110, 4'b0111: begin       // R-type: ADD..SRL
                reg_write = 1'b1;
                alu_op    = opcode[2:0];
            end
            4'b1000: begin reg_write = 1'b1; mem_read = 1'b1; wb_sel = 2'b01; end   // LOAD
            4'b1001: begin mem_write = 1'b1; reg2_sel = 1'b1; end                   // STORE
            4'b1010: begin reg_write = 1'b1; wb_sel = 2'b10; end                    // LI
            4'b1011: begin reg_write = 1'b1; alu_src = 1'b1; end                    // ADDI (alu_op = ADD)
            4'b1100: begin alu_op = 3'b001; reg2_sel = 1'b1; branch = 1'b1; end     // BEQ (compare with SUB)
            4'b1101: begin alu_op = 3'b001; reg2_sel = 1'b1; branch = 1'b1; br_ne = 1'b1; end  // BNE
            4'b1110: begin jump = 1'b1; end                                         // JMP
            4'b1111: begin halt = 1'b1; end                                         // HALT
            default: ;
        endcase
    end
endmodule
`default_nettype wire

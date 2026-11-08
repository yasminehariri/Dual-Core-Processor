// ============================================================================
// CCEE 324 Dual-Core Processor  |  alu.v
// Purpose : 8-bit ALU: ADD SUB AND OR XOR NOR SLL SRL + Zero/Carry/Overflow
// Spec    : Scope document v2.3, Section 13.3
// Author  : Yasmine (RTL lead)
// Status  : COMPLETE
// ============================================================================
`timescale 1ns/1ps
`default_nettype none
module alu (
    input  wire [7:0] a,         // operand A = register Rs (read port 1)
    input  wire [7:0] b,         // operand B = register Rt, or sign-extended imm6
    input  wire [2:0] alu_op,    // operation select = opcode[2:0]
    output reg  [7:0] result,
    output wire       zero,      // 1 when result == 8'h00
    output reg        carry,     // ADD: sum[8]; SUB: borrow = ~sum[8]
    output reg        overflow   // signed overflow for ADD and SUB
);
    // ALU operation codes (= opcode[2:0])
    localparam OP_ADD = 3'b000, OP_SUB = 3'b001, OP_AND = 3'b010, OP_OR  = 3'b011,
               OP_XOR = 3'b100, OP_NOR = 3'b101, OP_SLL = 3'b110, OP_SRL = 3'b111;

    // One 9-bit adder serves both ADD and SUB:
    //   ADD: A + B          (b_in = B,  cin = 0)
    //   SUB: A + ~B + 1     (b_in = ~B, cin = 1)  two's complement subtraction
    wire       is_sub = (alu_op == OP_SUB);
    wire [7:0] b_in   = is_sub ? ~b : b;
    wire [8:0] sum    = {1'b0, a} + {1'b0, b_in} + {8'b0, is_sub};

    always @(*) begin
        // defaults: no flags, so every case is fully specified (no latches)
        result   = 8'h00;
        carry    = 1'b0;
        overflow = 1'b0;
        case (alu_op)
            OP_ADD: begin
                result   = sum[7:0];
                carry    = sum[8];                                     // carry out of bit 7
                overflow = (a[7] == b[7]) && (result[7] != a[7]);      // pos+pos=neg or neg+neg=pos
            end
            OP_SUB: begin
                result   = sum[7:0];
                carry    = ~sum[8];                                    // borrow: 1 when a < b (unsigned)
                overflow = (a[7] != b[7]) && (result[7] != a[7]);      // pos-neg=neg or neg-pos=pos
            end
            OP_AND: result = a & b;
            OP_OR : result = a | b;
            OP_XOR: result = a ^ b;
            OP_NOR: result = ~(a | b);
            OP_SLL: result = a << b[2:0];                              // shift amount 0..7, zeros in
            OP_SRL: result = a >> b[2:0];                              // logical: zeros in from the left
            default: result = 8'h00;
        endcase
    end

    assign zero = (result == 8'h00);
endmodule
`default_nettype wire

// ============================================================================
// tb_alu.v - self-checking test of the ALU (Scope v2.3, Section 13.3 + 16)
// Written from the spec: every expected value below comes from the spec's
// rules, not from the ALU code.
// ============================================================================
`timescale 1ns/1ps
module tb_alu;
    reg  [7:0] a, b;
    reg  [2:0] op;
    wire [7:0] result;
    wire       zero, carry, overflow;

    alu dut (.a(a), .b(b), .alu_op(op), .result(result), .zero(zero), .carry(carry), .overflow(overflow));

    integer checks = 0, errors = 0;
    task check8(input [8*48-1:0] name, input [7:0] got, input [7:0] exp);
        begin checks = checks + 1;
            if (got === exp) $display("PASS  %0s  (got %h)", name, got);
            else begin errors = errors + 1; $display("FAIL  %0s  got %h, expected %h", name, got, exp); end
        end endtask
    task check1(input [8*48-1:0] name, input got, input exp);
        begin checks = checks + 1;
            if (got === exp) $display("PASS  %0s  (got %b)", name, got);
            else begin errors = errors + 1; $display("FAIL  %0s  got %b, expected %b", name, got, exp); end
        end endtask
    task summary;
        begin if (errors == 0) $display("ALL PASS (%0d checks)", checks);
              else             $display("FAILED %0d of %0d", errors, checks); end endtask

    // apply inputs, wait, then check result and all three flags
    task t(input [8*40-1:0] name, input [2:0] o, input [7:0] x, input [7:0] y,
           input [7:0] er, input ez, input ec, input ev);
        begin
            op = o; a = x; b = y; #1;
            check8({name, " result"},   result,   er);
            check1({name, " zero"},     zero,     ez);
            check1({name, " carry"},    carry,    ec);
            check1({name, " overflow"}, overflow, ev);
        end
    endtask

    localparam ADD = 3'b000, SUB = 3'b001, AND_ = 3'b010, OR_ = 3'b011,
               XOR_ = 3'b100, NOR_ = 3'b101, SLL = 3'b110, SRL = 3'b111;

    initial begin #10000; $display("FAIL  timeout"); errors = errors + 1; summary; $finish; end

    initial begin
        $dumpfile("docs/waves/dump_alu.vcd");
        $dumpvars(0, tb_alu);
        //  name                    op    A      B      result  Z  C  V
        // ---- ADD ----
        t("ADD 12+5",              ADD, 8'h0C, 8'h05, 8'h11,  0, 0, 0);
        t("ADD FF+01 wraps",       ADD, 8'hFF, 8'h01, 8'h00,  1, 1, 0);
        t("ADD 7F+01 overflow",    ADD, 8'h7F, 8'h01, 8'h80,  0, 0, 1);
        t("ADD 80+80 C and V",     ADD, 8'h80, 8'h80, 8'h00,  1, 1, 1);
        t("ADD 0+0 zero",          ADD, 8'h00, 8'h00, 8'h00,  1, 0, 0);
        // ---- SUB ----
        t("SUB 07-05",             SUB, 8'h07, 8'h05, 8'h02,  0, 0, 0);
        t("SUB 05-07 borrow",      SUB, 8'h05, 8'h07, 8'hFE,  0, 1, 0);
        t("SUB 05-05 zero",        SUB, 8'h05, 8'h05, 8'h00,  1, 0, 0);
        t("SUB 80-01 overflow",    SUB, 8'h80, 8'h01, 8'h7F,  0, 0, 1);
        t("SUB 7F-FF overflow",    SUB, 8'h7F, 8'hFF, 8'h80,  0, 1, 1);
        t("SUB 11-05 demo1",       SUB, 8'h11, 8'h05, 8'h0C,  0, 0, 0);
        // ---- logic ----
        t("AND F0&3C",             AND_, 8'hF0, 8'h3C, 8'h30, 0, 0, 0);
        t("AND 0F&F0 zero",        AND_, 8'h0F, 8'hF0, 8'h00, 1, 0, 0);
        t("OR  F0|0F",             OR_,  8'hF0, 8'h0F, 8'hFF, 0, 0, 0);
        t("XOR 05^03",             XOR_, 8'h05, 8'h03, 8'h06, 0, 0, 0);
        t("XOR AA^AA zero",        XOR_, 8'hAA, 8'hAA, 8'h00, 1, 0, 0);
        t("NOR 00 gives FF",       NOR_, 8'h00, 8'h00, 8'hFF, 0, 0, 0);
        t("NOR F0|0F gives 00",    NOR_, 8'hF0, 8'h0F, 8'h00, 1, 0, 0);
        // ---- shifts (amount = B[2:0]) ----
        t("SLL 05<<3",             SLL, 8'h05, 8'h03, 8'h28,  0, 0, 0);
        t("SLL by 0",              SLL, 8'h81, 8'h00, 8'h81,  0, 0, 0);
        t("SLL by 7",              SLL, 8'h01, 8'h07, 8'h80,  0, 0, 0);
        t("SLL B=0B uses 3 bits",  SLL, 8'h01, 8'h0B, 8'h08,  0, 0, 0);
        t("SLL bits fall off",     SLL, 8'h80, 8'h01, 8'h00,  1, 0, 0);
        t("SRL F0>>4",             SRL, 8'hF0, 8'h04, 8'h0F,  0, 0, 0);
        t("SRL by 7 zeros in",     SRL, 8'h80, 8'h07, 8'h01,  0, 0, 0);
        t("SRL by 0",              SRL, 8'hA5, 8'h00, 8'hA5,  0, 0, 0);
        summary;
        $finish;
    end
endmodule

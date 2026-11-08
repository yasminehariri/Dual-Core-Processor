// tb_control_unit.v - all 16 opcodes against the table in Section 13.5,
// plus the decoder's field extraction (Section 12).
`timescale 1ns/1ps
module tb_control_unit;
    reg  [3:0] opcode = 0;
    wire reg_write, alu_src, mem_read, mem_write, reg2_sel, branch, br_ne, jump, halt;
    wire [2:0] alu_op; wire [1:0] wb_sel;
    control_unit dut (.opcode(opcode), .reg_write(reg_write), .alu_src(alu_src), .alu_op(alu_op), .mem_read(mem_read),
        .mem_write(mem_write), .wb_sel(wb_sel), .reg2_sel(reg2_sel), .branch(branch), .br_ne(br_ne), .jump(jump), .halt(halt));
    reg  [15:0] instr = 0;
    wire [3:0] d_op; wire [2:0] d_rd, d_rs, d_rt; wire [7:0] d_imm, d_addr; wire [5:0] d_off;
    decoder dec (.instr(instr), .opcode(d_op), .rd(d_rd), .rs(d_rs), .rt(d_rt), .imm6_sext(d_imm), .off6(d_off), .addr8(d_addr));
    integer checks = 0, errors = 0;
    task check8(input [8*48-1:0] name, input [7:0] got, input [7:0] exp);
        begin checks = checks + 1;
            if (got === exp) $display("PASS  %0s  (got %h)", name, got);
            else begin errors = errors + 1; $display("FAIL  %0s  got %h, expected %h", name, got, exp); end
        end endtask
    task check16(input [8*48-1:0] name, input [15:0] got, input [15:0] exp);
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
    initial begin #200000; $display("FAIL  timeout"); errors = errors + 1; summary; $finish; end
    // all 14 control bits packed in table order: RegWr ALUSrc ALUOp[2:0] MemRd MemWr WBSel[1:0] Reg2Sel Branch BrNE Jump Halt
    wire [13:0] ctl = {reg_write, alu_src, alu_op, mem_read, mem_write, wb_sel, reg2_sel, branch, br_ne, jump, halt};
    task row(input [8*8-1:0] name, input [3:0] op, input [13:0] exp);
        begin opcode = op; #1;
            checks = checks + 1;
            if (ctl === exp) $display("PASS  %0s  control = %b", name, ctl);
            else begin errors = errors + 1; $display("FAIL  %0s  control = %b, expected %b", name, ctl, exp); end
        end endtask
    initial begin
        $dumpfile("docs/waves/dump_control_unit.vcd"); $dumpvars(0, tb_control_unit);
        //            op       RW AS ALUOp MR MW WB  R2 Br NE J  H
        row("ADD",   4'b0000, 14'b1_0_000_0_0_00_0_0_0_0_0);
        row("SUB",   4'b0001, 14'b1_0_001_0_0_00_0_0_0_0_0);
        row("AND",   4'b0010, 14'b1_0_010_0_0_00_0_0_0_0_0);
        row("OR",    4'b0011, 14'b1_0_011_0_0_00_0_0_0_0_0);
        row("XOR",   4'b0100, 14'b1_0_100_0_0_00_0_0_0_0_0);
        row("NOR",   4'b0101, 14'b1_0_101_0_0_00_0_0_0_0_0);
        row("SLL",   4'b0110, 14'b1_0_110_0_0_00_0_0_0_0_0);
        row("SRL",   4'b0111, 14'b1_0_111_0_0_00_0_0_0_0_0);
        row("LOAD",  4'b1000, 14'b1_0_000_1_0_01_0_0_0_0_0);
        row("STORE", 4'b1001, 14'b0_0_000_0_1_00_1_0_0_0_0);
        row("LI",    4'b1010, 14'b1_0_000_0_0_10_0_0_0_0_0);
        row("ADDI",  4'b1011, 14'b1_1_000_0_0_00_0_0_0_0_0);
        row("BEQ",   4'b1100, 14'b0_0_001_0_0_00_1_1_0_0_0);
        row("BNE",   4'b1101, 14'b0_0_001_0_0_00_1_1_1_0_0);
        row("JMP",   4'b1110, 14'b0_0_000_0_0_00_0_0_0_1_0);
        row("HALT",  4'b1111, 14'b0_0_000_0_0_00_0_0_0_0_1);
        // decoder fields
        instr = 16'h0650; #1;                              // ADD R3, R1, R2
        check8("decoder opcode", {4'h0, d_op}, 8'h00); check8("decoder rd", {5'd0, d_rd}, 8'd3);
        check8("decoder rs", {5'd0, d_rs}, 8'd1);      check8("decoder rt", {5'd0, d_rt}, 8'd2);
        instr = 16'hB4BF; #1;                              // ADDI R2, R2, -1
        check8("decoder imm6 -1 sign-extended", d_imm, 8'hFF);
        instr = 16'hB490; #1;                              // ADDI with imm6 = 0x10 (+16)
        check8("decoder imm6 +16", d_imm, 8'h10);
        instr = 16'hB4A0; #1;                              // imm6 = 0x20 (-32)
        check8("decoder imm6 -32", d_imm, 8'hE0);
        instr = 16'hC63E; #1;                              // BEQ R3, R0, -2
        check8("decoder off6", {2'b00, d_off}, 8'h3E);
        instr = 16'h9640; #1;                              // STORE R3, [0x40]
        check8("decoder addr8", d_addr, 8'h40);
        summary; $finish;
    end
endmodule

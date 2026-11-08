// ============================================================================
// tb_core.v - single-core integration test (Scope v2.3, Section 16)
//   Core A runs programs/core_all.hex : all 16 instructions + 4 pseudo-instructions,
//                                       branches taken / not taken, forward / backward
//   Core B runs programs/loop_test.hex : ADDI + BNE loop, 5+4+3+2+1 = 15
// Expected values come from the Python reference model of the ISA.
// Each core gets its own data memory (a shared_mem with port 1 unused).
// ============================================================================
`timescale 1ns/1ps
module tb_core;
    reg clk = 1'b0, rst = 1'b1;
    always #5 clk = ~clk;

    // ---- core A + its memory ----
    wire [7:0] a_addr, a_wdata, a_rdata, a_pc; wire a_we, a_halted; wire [15:0] a_cyc, a_ins; wire [63:0] a_regs;
    core #(.PROG("programs/core_all.hex")) coreA (.clk(clk), .rst(rst), .mem_rdata(a_rdata), .mem_addr(a_addr),
        .mem_wdata(a_wdata), .mem_we(a_we), .halted(a_halted), .pc(a_pc), .cycle_count(a_cyc), .instr_count(a_ins), .dbg_regs(a_regs));
    shared_mem #(.INIT("programs/data2.hex")) memA (.clk(clk), .addr0(a_addr), .wdata0(a_wdata), .we0(a_we), .rdata0(a_rdata),
        .addr1(8'h00), .wdata1(8'h00), .we1(1'b0), .rdata1());

    // ---- core B + its memory ----
    wire [7:0] b_addr, b_wdata, b_rdata, b_pc; wire b_we, b_halted; wire [15:0] b_cyc, b_ins; wire [63:0] b_regs;
    core #(.PROG("programs/loop_test.hex")) coreB (.clk(clk), .rst(rst), .mem_rdata(b_rdata), .mem_addr(b_addr),
        .mem_wdata(b_wdata), .mem_we(b_we), .halted(b_halted), .pc(b_pc), .cycle_count(b_cyc), .instr_count(b_ins), .dbg_regs(b_regs));
    shared_mem #(.INIT("programs/data2.hex")) memB (.clk(clk), .addr0(b_addr), .wdata0(b_wdata), .we0(b_we), .rdata0(b_rdata),
        .addr1(8'h00), .wdata1(8'h00), .we1(1'b0), .rdata1());

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

    // cycle-by-cycle trace of core A (the waveform shows the same)
    always @(posedge clk) if (!rst && !a_halted)
        $display("TRACE  cycle %0d  pc %0d  instr %h", a_cyc, a_pc, coreA.instr);

    initial begin
        $dumpfile("docs/waves/dump_core.vcd"); $dumpvars(0, tb_core);
        @(negedge clk); @(negedge clk); rst = 0;
        wait (a_halted && b_halted);
        @(negedge clk);
        // ---- core A: registers {R7..R0} ----
        check8("A: R1 loop counter ends at 0",   a_regs[15:8],  8'h00);
        check8("A: R2 loop sum = 6",             a_regs[23:16], 8'h06);
        check8("A: R3 = 2 (LI)",                 a_regs[31:24], 8'h02);
        check8("A: R4 = 0 (CLR)",                a_regs[39:32], 8'h00);
        check8("A: R5 = 77 (branch skipped EE)", a_regs[47:40], 8'h77);
        check8("A: R6 = 2F (LOAD + 2 ADDI)",     a_regs[55:48], 8'h2F);
        check8("A: R7 = D0 (MOV + NOT)",         a_regs[63:56], 8'hD0);
        check8("A: R0 never written",            a_regs[7:0],   8'h00);
        // ---- core A: memory ----
        check8("A: Mem[20] ADD 12+5",            memA.mem[8'h20], 8'h11);
        check8("A: Mem[21] NOR",                 memA.mem[8'h21], 8'hF2);
        check8("A: Mem[22] SLL 5<<2",            memA.mem[8'h22], 8'h14);
        check8("A: Mem[23] SRL 12>>2",           memA.mem[8'h23], 8'h03);
        check8("A: Mem[24] ADDI -1 then +31",    memA.mem[8'h24], 8'h2F);
        check8("A: Mem[25] NOT",                 memA.mem[8'h25], 8'hD0);
        check8("A: Mem[26] BEQ taken, BNE not",  memA.mem[8'h26], 8'h77);
        check8("A: Mem[27] backward loop",       memA.mem[8'h27], 8'h06);
        // ---- core A: control ----
        check16("A: cycle_count = 43",           a_cyc, 16'd43);
        check16("A: instr_count = cycle_count",  a_ins, a_cyc);
        check8("A: PC holds on HALT (39)",       a_pc,  8'd39);
        repeat (3) @(negedge clk);
        check8("A: PC still 39 after 3 cycles",  a_pc,  8'd39);
        check16("A: counters stopped",           a_cyc, 16'd43);
        // ---- core B: loop test ----
        check8("B: Mem[90] = 5+4+3+2+1 = 0F",    memB.mem[8'h90], 8'h0F);
        check8("B: R2 = 0F",                     b_regs[23:16], 8'h0F);
        check16("B: 19 cycles",                  b_cyc, 16'd19);
        summary; $finish;
    end
endmodule

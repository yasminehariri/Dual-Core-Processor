// ============================================================================
// tb_dual_core.v - full dual-core test (Scope v2.3, Section 16)
// Five complete processors run side by side, one per scenario:
//   demo1  independent cores + shared memory      (required instructions only)
//   demo2  flag synchronization with a spin-wait  (bonus instructions)
//   demo3  parallel sum on two cores
//   single the same sum on one core (core 1 just halts)
//   confl  both cores store to 0x50 in the same cycle: Core 0 must win
// Expected values are the ones published in the scope document.
// ============================================================================
`timescale 1ns/1ps
module tb_dual_core;
    reg clk = 1'b0, rst = 1'b1;
    always #5 clk = ~clk;
    wire demo1_h0, demo1_h1, demo1_both; wire [7:0] demo1_pc0, demo1_pc1; wire [63:0] demo1_r0, demo1_r1; wire [15:0] demo1_c0, demo1_c1;
    dual_core_top #(.PROG0("programs/demo1_core0.hex"), .PROG1("programs/demo1_core1.hex"), .DATA("programs/data1.hex")) demo1 (
        .clk(clk), .rst(rst), .halted0(demo1_h0), .halted1(demo1_h1), .both_halted(demo1_both),
        .pc0(demo1_pc0), .pc1(demo1_pc1), .regs0(demo1_r0), .regs1(demo1_r1), .cycles0(demo1_c0), .cycles1(demo1_c1));
    wire demo2_h0, demo2_h1, demo2_both; wire [7:0] demo2_pc0, demo2_pc1; wire [63:0] demo2_r0, demo2_r1; wire [15:0] demo2_c0, demo2_c1;
    dual_core_top #(.PROG0("programs/demo2_core0.hex"), .PROG1("programs/demo2_core1.hex"), .DATA("programs/data2.hex")) demo2 (
        .clk(clk), .rst(rst), .halted0(demo2_h0), .halted1(demo2_h1), .both_halted(demo2_both),
        .pc0(demo2_pc0), .pc1(demo2_pc1), .regs0(demo2_r0), .regs1(demo2_r1), .cycles0(demo2_c0), .cycles1(demo2_c1));
    wire demo3_h0, demo3_h1, demo3_both; wire [7:0] demo3_pc0, demo3_pc1; wire [63:0] demo3_r0, demo3_r1; wire [15:0] demo3_c0, demo3_c1;
    dual_core_top #(.PROG0("programs/demo3_core0.hex"), .PROG1("programs/demo3_core1.hex"), .DATA("programs/data3.hex")) demo3 (
        .clk(clk), .rst(rst), .halted0(demo3_h0), .halted1(demo3_h1), .both_halted(demo3_both),
        .pc0(demo3_pc0), .pc1(demo3_pc1), .regs0(demo3_r0), .regs1(demo3_r1), .cycles0(demo3_c0), .cycles1(demo3_c1));
    wire single_h0, single_h1, single_both; wire [7:0] single_pc0, single_pc1; wire [63:0] single_r0, single_r1; wire [15:0] single_c0, single_c1;
    dual_core_top #(.PROG0("programs/demo3_single.hex"), .PROG1("programs/halt.hex"), .DATA("programs/data3.hex")) single (
        .clk(clk), .rst(rst), .halted0(single_h0), .halted1(single_h1), .both_halted(single_both),
        .pc0(single_pc0), .pc1(single_pc1), .regs0(single_r0), .regs1(single_r1), .cycles0(single_c0), .cycles1(single_c1));
    wire confl_h0, confl_h1, confl_both; wire [7:0] confl_pc0, confl_pc1; wire [63:0] confl_r0, confl_r1; wire [15:0] confl_c0, confl_c1;
    dual_core_top #(.PROG0("programs/conflict_core0.hex"), .PROG1("programs/conflict_core1.hex"), .DATA("programs/data2.hex")) confl (
        .clk(clk), .rst(rst), .halted0(confl_h0), .halted1(confl_h1), .both_halted(confl_both),
        .pc0(confl_pc0), .pc1(confl_pc1), .regs0(confl_r0), .regs1(confl_r1), .cycles0(confl_c0), .cycles1(confl_c1));
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

    // trace of Demo 2's Core 1 spin-waiting on the flag
    always @(posedge clk) if (!rst && !demo2_h1)
        $display("TRACE demo2 core1  cycle %0d  pc %0d  flag Mem[F0] = %h", demo2_c1, demo2_pc1, demo2.mem.mem[8'hF0]);

    integer t_single, t_dual;
    initial begin
        $dumpfile("docs/waves/dump_dual_core.vcd"); $dumpvars(0, tb_dual_core);
        @(negedge clk); @(negedge clk); rst = 0;
        wait (demo1_both && demo2_both && demo3_both && single_both && confl_both);
        @(negedge clk);

        // ---------- Demo 1 ----------
        check8("demo1 core0 R1 = 0C", demo1_r0[15:8],  8'h0C);
        check8("demo1 core0 R2 = 05", demo1_r0[23:16], 8'h05);
        check8("demo1 core0 R3 = 11", demo1_r0[31:24], 8'h11);
        check8("demo1 core1 R1 = 05 (differs from core0 R1)", demo1_r1[15:8], 8'h05);
        check8("demo1 core1 R2 = 03", demo1_r1[23:16], 8'h03);
        check8("demo1 core1 R3 = 28 (SLL)", demo1_r1[31:24], 8'h28);
        check8("demo1 core1 R4 = 06 (XOR)", demo1_r1[39:32], 8'h06);
        check8("demo1 core1 R5 = 11 (read from core0)", demo1_r1[47:40], 8'h11);
        check8("demo1 core1 R6 = 0C", demo1_r1[55:48], 8'h0C);
        check8("demo1 Mem[40] = 11", demo1.mem.mem[8'h40], 8'h11);
        check8("demo1 Mem[41] = 0C", demo1.mem.mem[8'h41], 8'h0C);
        check16("demo1 core0 halts after 5 cycles", demo1_c0, 16'd5);
        check16("demo1 core1 halts after 8 cycles", demo1_c1, 16'd8);

        // ---------- Demo 2 ----------
        check8("demo2 Mem[80] = 2A (42)", demo2.mem.mem[8'h80], 8'h2A);
        check8("demo2 Mem[F0] flag = 01", demo2.mem.mem[8'hF0], 8'h01);
        check8("demo2 Mem[81] = 28 (40)", demo2.mem.mem[8'h81], 8'h28);
        check16("demo2 core0 7 cycles", demo2_c0, 16'd7);
        check16("demo2 core1 13 cycles", demo2_c1, 16'd13);

        // ---------- Demo 3 ----------
        check8("demo3 Mem[80] partial = 24 (36)", demo3.mem.mem[8'h80], 8'h24);
        check8("demo3 Mem[82] sum = 88 (136)", demo3.mem.mem[8'h82], 8'h88);
        check16("demo3 core0 19 cycles", demo3_c0, 16'd19);
        check16("demo3 core1 25 cycles", demo3_c1, 16'd25);
        check8("single Mem[82] sum = 88 (136)", single.mem.mem[8'h82], 8'h88);
        check16("single core 33 cycles", single_c0, 16'd33);

        // ---------- Conflict ----------
        check8("conflict Mem[50] = AA (Core 0 wins)", confl.mem.mem[8'h50], 8'hAA);

        // ---------- Performance summary ----------
        t_single = single_c0;
        t_dual   = (demo3_c0 > demo3_c1) ? demo3_c0 : demo3_c1;    // T_dual = max(C0, C1), never the sum
        $display("PERF  demo3: single core %0d cycles, dual core %0d cycles, speedup %0d.%02d x",
                 t_single, t_dual, t_single / t_dual, (t_single * 100 / t_dual) % 100);
        summary; $finish;
    end
endmodule

// ============================================================================
// tb_template.v - copy this file to start a new testbench (run_all skips it).
//   1. Rename the file AND the module to tb_<thing>.
//   2. Instantiate the module under test.
//   3. Write checks with check8 / check1 between the two marked lines.
// Rules (Scope v2.3, Section 16): change inputs on the FALLING edge, check
// 1 time unit after an edge, every check has a name, summary line at the end.
// ============================================================================
`timescale 1ns/1ps
module tb_template;
    // ---- clock and reset ---------------------------------------------------
    reg clk = 1'b0;
    reg rst = 1'b1;
    always #5 clk = ~clk;                       // 10 ns period

    // ---- check bookkeeping (copy this block into every testbench) ---------
    integer checks = 0, errors = 0;
    task check8(input [8*48-1:0] name, input [7:0] got, input [7:0] exp);
        begin
            checks = checks + 1;
            if (got === exp) $display("PASS  %0s  (got %h)", name, got);
            else begin errors = errors + 1; $display("FAIL  %0s  got %h, expected %h", name, got, exp); end
        end
    endtask
    task check1(input [8*48-1:0] name, input got, input exp);
        begin
            checks = checks + 1;
            if (got === exp) $display("PASS  %0s  (got %b)", name, got);
            else begin errors = errors + 1; $display("FAIL  %0s  got %b, expected %b", name, got, exp); end
        end
    endtask
    task summary;
        begin
            if (errors == 0) $display("ALL PASS (%0d checks)", checks);
            else             $display("FAILED %0d of %0d", errors, checks);
        end
    endtask

    // ---- timeout guard: no simulation may run forever ----------------------
    initial begin #100000; $display("FAIL  timeout"); errors = errors + 1; summary; $finish; end

    // ---- module under test goes here ---------------------------------------

    initial begin
        $dumpfile("docs/waves/dump_template.vcd");
        $dumpvars(0, tb_template);
        @(negedge clk); rst = 1'b0;
        // ======== checks start ========
        check1("example: reset released", rst, 1'b0);
        // ======== checks end ==========
        summary;
        $finish;
    end
endmodule

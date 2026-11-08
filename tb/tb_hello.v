// ============================================================================
// tb_hello.v - install check. Shows a clock in the wave window and prints
// the standard summary line so run_all can read it.
// ============================================================================
`timescale 1ns/1ps
module tb_hello;
    reg clk = 1'b0;
    always #5 clk = ~clk;             // 100 MHz clock, 10 ns period
    integer ticks = 0;
    always @(posedge clk) ticks = ticks + 1;

    initial begin
        $dumpfile("docs/waves/dump_hello.vcd");
        $dumpvars(0, tb_hello);
        #100;
        if (ticks == 10) $display("PASS  clock ran 10 cycles");
        else             $display("FAIL  clock ran %0d cycles, expected 10", ticks);
        if (ticks == 10) $display("ALL PASS (1 checks)");
        else             $display("FAILED 1 of 1");
        $finish;
    end
endmodule

// tb_regfile.v - register file test (Scope v2.3, Sections 13.4 and 16)
`timescale 1ns/1ps
module tb_regfile;
    reg clk = 1'b0, rst = 1'b1;
    always #5 clk = ~clk;
    reg  [2:0] ra1 = 0, ra2 = 0, wa = 0;
    reg  [7:0] wd = 0;
    reg        we = 0;
    wire [7:0] rd1, rd2, r0, r1, r2, r3, r4, r5, r6, r7;
    regfile dut (.clk(clk), .rst(rst), .ra1(ra1), .ra2(ra2), .wa(wa), .wd(wd), .we(we), .rd1(rd1), .rd2(rd2),
                 .dbg_r0(r0), .dbg_r1(r1), .dbg_r2(r2), .dbg_r3(r3), .dbg_r4(r4), .dbg_r5(r5), .dbg_r6(r6), .dbg_r7(r7));
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
    integer i;
    task wr(input [2:0] a, input [7:0] d);        // one write: set on falling edge, lands on rising edge
        begin @(negedge clk); we = 1; wa = a; wd = d; @(posedge clk); #1; we = 0; end endtask
    initial begin
        $dumpfile("docs/waves/dump_regfile.vcd"); $dumpvars(0, tb_regfile);
        @(posedge clk); #1;                              // reset applied at this edge
        check8("reset clears R0", r0, 8'h00);
        check8("reset clears R7", r7, 8'h00);
        @(negedge clk); rst = 0;
        // write a different value into every register, then read all back on both ports
        for (i = 0; i < 8; i = i + 1) wr(i, 8'h10 + i * 8'h11);
        for (i = 0; i < 8; i = i + 1) begin
            ra1 = i; ra2 = 7 - i; #1;
            check8("read port 1 after write", rd1, 8'h10 + i * 8'h11);
            check8("read port 2 after write", rd2, 8'h10 + (7 - i) * 8'h11);
        end
        // we = 0 must block a write
        @(negedge clk); we = 0; wa = 3; wd = 8'hEE; @(posedge clk); #1;
        ra1 = 3; #1; check8("we=0 blocks write", rd1, 8'h43);
        // read-during-write: before the edge the old value, after the edge the new one
        @(negedge clk); we = 1; wa = 1; wd = 8'h55; ra1 = 1; #1;
        check8("read before write edge (old)", rd1, 8'h21);
        @(posedge clk); #1;
        check8("read after write edge (new)", rd1, 8'h55);
        we = 0;
        // synchronous reset clears everything again
        @(negedge clk); rst = 1; @(posedge clk); #1; rst = 0;
        check8("second reset clears R1", r1, 8'h00);
        check8("second reset clears R5", r5, 8'h00);
        summary; $finish;
    end
endmodule

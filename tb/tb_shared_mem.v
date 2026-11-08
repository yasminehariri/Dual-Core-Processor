// tb_shared_mem.v - dual-port shared memory test (Scope v2.3, Sections 13.6 and 16)
`timescale 1ns/1ps
module tb_shared_mem;
    reg clk = 1'b0;
    always #5 clk = ~clk;
    reg [7:0] a0 = 0, d0 = 0, a1 = 0, d1 = 0; reg w0 = 0, w1 = 0;
    wire [7:0] q0, q1;
    shared_mem #(.INIT("programs/data1.hex")) dut (.clk(clk), .addr0(a0), .wdata0(d0), .we0(w0), .rdata0(q0),
                                                  .addr1(a1), .wdata1(d1), .we1(w1), .rdata1(q1));
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
    initial begin
        $dumpfile("docs/waves/dump_shared_mem.vcd"); $dumpvars(0, tb_shared_mem);
        #1;
        a0 = 8'h00; a1 = 8'h02; #1;
        check8("init: data1.hex byte 0 on port 0", q0, 8'h0C);
        check8("init: data1.hex byte 2 on port 1", q1, 8'h03);
        a0 = 8'h77; a1 = 8'hFF; #1;
        check8("untouched byte reads 00 (not X)", q0, 8'h00);
        check8("last byte reads 00 (not X)", q1, 8'h00);
        // port 0 writes, port 1 reads it back next cycle
        @(negedge clk); a0 = 8'h40; d0 = 8'h11; w0 = 1; a1 = 8'h40; #1;
        check8("read during write sees old value", q1, 8'h00);
        @(posedge clk); #1; w0 = 0;
        check8("port 1 sees port 0's write next cycle", q1, 8'h11);
        // port 1 writes, port 0 reads it
        @(negedge clk); a1 = 8'h41; d1 = 8'h22; w1 = 1; a0 = 8'h41;
        @(posedge clk); #1; w1 = 0;
        check8("port 0 sees port 1's write", q0, 8'h22);
        // both write different addresses in the same cycle
        @(negedge clk); a0 = 8'h60; d0 = 8'hA0; w0 = 1; a1 = 8'h61; d1 = 8'hB1; w1 = 1;
        @(posedge clk); #1; w0 = 0; w1 = 0;
        check8("simultaneous write, port 0 address", q0, 8'hA0);
        check8("simultaneous write, port 1 address", q1, 8'hB1);
        // both write the SAME address in the same cycle: Core 0 must win
        @(negedge clk); a0 = 8'h50; d0 = 8'hAA; w0 = 1; a1 = 8'h50; d1 = 8'h55; w1 = 1;
        @(posedge clk); #1; w0 = 0; w1 = 0;
        check8("conflict: Core 0 wins (port 0 view)", q0, 8'hAA);
        check8("conflict: Core 0 wins (port 1 view)", q1, 8'hAA);
        summary; $finish;
    end
endmodule

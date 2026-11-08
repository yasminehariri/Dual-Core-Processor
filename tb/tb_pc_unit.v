// tb_pc_unit.v - program counter test (Scope v2.3, Sections 13.2 and 16)
`timescale 1ns/1ps
module tb_pc_unit;
    reg clk = 1'b0, rst = 1'b1;
    always #5 clk = ~clk;
    reg halt = 0, jump = 0, bt = 0; reg [7:0] ja = 0; reg [5:0] off = 0;
    wire [7:0] pc; wire halted;
    pc_unit dut (.clk(clk), .rst(rst), .halt(halt), .jump(jump), .branch_taken(bt), .jump_addr(ja), .off6(off), .pc(pc), .halted(halted));
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
    task step; begin @(posedge clk); #1; end endtask
    initial begin
        $dumpfile("docs/waves/dump_pc_unit.vcd"); $dumpvars(0, tb_pc_unit);
        step; check8("reset gives 0", pc, 8'h00); check1("not halted after reset", halted, 1'b0);
        @(negedge clk); rst = 0;
        step; check8("increment to 1", pc, 8'h01);
        step; check8("increment to 2", pc, 8'h02);
        @(negedge clk); jump = 1; ja = 8'h10; step; jump = 0;
        check8("jump to 0x10", pc, 8'h10);
        @(negedge clk); bt = 1; off = 6'd2; step; bt = 0;
        check8("branch +2 from 0x10 -> 0x13", pc, 8'h13);
        @(negedge clk); bt = 1; off = 6'b111110; step; bt = 0;
        check8("branch -2 from 0x13 -> 0x12", pc, 8'h12);
        @(negedge clk); bt = 1; off = 6'b100000; step; bt = 0;
        check8("branch -32 from 0x12 -> 0xF3 (wraps)", pc, 8'hF3);
        @(negedge clk); bt = 1; off = 6'b011111; step; bt = 0;
        check8("branch +31 from 0xF3 -> 0x13 (wraps)", pc, 8'h13);
        @(negedge clk); jump = 1; ja = 8'hFF; step; jump = 0;
        step; check8("wrap 0xFF -> 0x00", pc, 8'h00);
        @(negedge clk); jump = 1; bt = 1; ja = 8'h40; off = 6'd5; step; jump = 0; bt = 0;
        check8("jump wins over branch", pc, 8'h40);
        @(negedge clk); halt = 1; jump = 1; ja = 8'h99; step; halt = 0; jump = 0;
        check8("halt holds PC (beats jump)", pc, 8'h40); check1("halted set", halted, 1'b1);
        step; step; check8("still held after halt", pc, 8'h40); check1("halted stays", halted, 1'b1);
        @(negedge clk); rst = 1; step; rst = 0;
        check8("reset after halt gives 0", pc, 8'h00); check1("reset clears halted", halted, 1'b0);
        summary; $finish;
    end
endmodule

// tb_instr_mem.v - loads programs/test_encodings.hex and reads every word back;
// unused addresses must read HALT (0xF000). (Scope v2.3, Section 16)
`timescale 1ns/1ps
module tb_instr_mem;
    reg [7:0] addr = 0; wire [15:0] instr;
    instr_mem #(.PROG("programs/test_encodings.hex")) dut (.addr(addr), .instr(instr));
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
    reg [15:0] exp [0:15];
    integer i;
    initial begin
        $dumpfile("docs/waves/dump_instr_mem.vcd"); $dumpvars(0, tb_instr_mem);
        exp[0]=16'h0650; exp[1]=16'h18C8; exp[2]=16'h2A50; exp[3]=16'h3A50; exp[4]=16'h4850; exp[5]=16'h5CE0;
        exp[6]=16'h6650; exp[7]=16'h7650; exp[8]=16'h8220; exp[9]=16'h9640; exp[10]=16'hA205; exp[11]=16'hB4BF;
        exp[12]=16'hC63E; exp[13]=16'hD283; exp[14]=16'hE010; exp[15]=16'hF000;
        for (i = 0; i < 16; i = i + 1) begin addr = i; #1; check16("program word", instr, exp[i]); end
        addr = 8'd16;  #1; check16("unused address 16 is HALT", instr, 16'hF000);
        addr = 8'd128; #1; check16("unused address 128 is HALT", instr, 16'hF000);
        addr = 8'd255; #1; check16("unused address 255 is HALT", instr, 16'hF000);
        summary; $finish;
    end
endmodule

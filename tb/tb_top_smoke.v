// ============================================================================
// tb_top_smoke.v - proves the whole design (top + 2 cores + memory) compiles
// and elaborates together. Replaced by tb_dual_core.v in Phase 3.
// ============================================================================
`timescale 1ns/1ps
module tb_top_smoke;
    reg clk = 1'b0, rst = 1'b1;
    always #5 clk = ~clk;
    wire halted0, halted1, both_halted;
    wire [7:0] pc0, pc1; wire [63:0] regs0, regs1; wire [15:0] cycles0, cycles1;

    dual_core_top dut (.clk(clk), .rst(rst), .halted0(halted0), .halted1(halted1), .both_halted(both_halted),
        .pc0(pc0), .pc1(pc1), .regs0(regs0), .regs1(regs1), .cycles0(cycles0), .cycles1(cycles1));

    initial begin
        $dumpfile("docs/waves/dump_top_smoke.vcd");
        $dumpvars(0, tb_top_smoke);
        #20 rst = 1'b0;
        #50;
        $display("PASS  design elaborated and ran 5 cycles");
        $display("ALL PASS (1 checks)");
        $finish;
    end
endmodule

// ============================================================================
// CCEE 324 Dual-Core Processor  |  core.v
// Purpose : One single-cycle CPU core: decoder, control unit, PC, instruction
//           memory, register file, ALU, the 4 datapath muxes and 2 counters
// Spec    : Scope document v2.3, Sections 13.2, 13.7 and 15
// Author  : Yasmine (RTL lead)
// Status  : COMPLETE (Tier A, single-cycle; PIPELINED is reserved for Tier B)
// ============================================================================
`timescale 1ns/1ps
`default_nettype none
module core #(
    parameter PROG      = "programs/core0.hex",
    parameter PIPELINED = 0                    // Tier B only; 0 = single-cycle
) (
    input  wire        clk,
    input  wire        rst,
    // shared memory port
    input  wire [7:0]  mem_rdata,
    output wire [7:0]  mem_addr,
    output wire [7:0]  mem_wdata,
    output wire        mem_we,
    // status and debug
    output wire        halted,
    output wire [7:0]  pc,
    output reg  [15:0] cycle_count,
    output reg  [15:0] instr_count,
    output wire [63:0] dbg_regs              // {R7, R6, R5, R4, R3, R2, R1, R0}
);
    // ---------------- FETCH ----------------
    wire [15:0] instr;
    instr_mem #(.PROG(PROG)) imem (.addr(pc), .instr(instr));

    // ---------------- DECODE ----------------
    wire [3:0] opcode;
    wire [2:0] rd, rs, rt;
    wire [7:0] imm6_sext, addr8;
    wire [5:0] off6;
    decoder dec (.instr(instr), .opcode(opcode), .rd(rd), .rs(rs), .rt(rt),
                 .imm6_sext(imm6_sext), .off6(off6), .addr8(addr8));

    wire       reg_write, alu_src, mem_read, mem_write, reg2_sel, branch, br_ne, jump, halt;
    wire [2:0] alu_op;
    wire [1:0] wb_sel;
    control_unit ctrl (.opcode(opcode), .reg_write(reg_write), .alu_src(alu_src), .alu_op(alu_op),
                       .mem_read(mem_read), .mem_write(mem_write), .wb_sel(wb_sel), .reg2_sel(reg2_sel),
                       .branch(branch), .br_ne(br_ne), .jump(jump), .halt(halt));

    // ---------------- REGISTER READ ----------------
    // Mux 1 (Reg2 mux): STORE and branches read inst[11:9] on port 2
    wire [2:0] ra2 = reg2_sel ? rd : rt;
    wire [7:0] rd1, rd2, wb_data;
    wire [7:0] r0, r1, r2, r3, r4, r5, r6, r7;
    regfile rf (.clk(clk), .rst(rst), .ra1(rs), .ra2(ra2), .wa(rd), .wd(wb_data),
                .we(reg_write & ~halted),                     // safety net: nothing is written after HALT
                .rd1(rd1), .rd2(rd2),
                .dbg_r0(r0), .dbg_r1(r1), .dbg_r2(r2), .dbg_r3(r3), .dbg_r4(r4), .dbg_r5(r5), .dbg_r6(r6), .dbg_r7(r7));

    // ---------------- EXECUTE ----------------
    // Mux 2 (ALU-B mux): ADDI uses the sign-extended immediate
    wire [7:0] alu_b = alu_src ? imm6_sext : rd2;
    wire [7:0] alu_result;
    wire       zero, carry, overflow;
    alu alu_u (.a(rd1), .b(alu_b), .alu_op(alu_op), .result(alu_result),
               .zero(zero), .carry(carry), .overflow(overflow));

    // ---------------- MEMORY ----------------
    assign mem_addr  = addr8;
    assign mem_wdata = rd2;                                  // STORE data comes from inst[11:9] via the Reg2 mux
    assign mem_we    = mem_write & ~halted;

    // ---------------- WRITE BACK ----------------
    // Mux 3 (WB mux): ALU result, loaded byte, or LI immediate
    assign wb_data = (wb_sel == 2'b01) ? mem_rdata :
                     (wb_sel == 2'b10) ? addr8 :
                                         alu_result;

    // ---------------- NEXT PC ----------------
    // Mux 4 lives inside pc_unit. BEQ/BNE compare with SUB: equal <=> zero = 1
    wire branch_taken = branch & (zero ^ br_ne);
    pc_unit pcu (.clk(clk), .rst(rst), .halt(halt), .jump(jump), .branch_taken(branch_taken),
                 .jump_addr(addr8), .off6(off6), .pc(pc), .halted(halted));

    // ---------------- PERFORMANCE COUNTERS ----------------
    // Both count every executed cycle, including the cycle in which HALT executes.
    always @(posedge clk) begin
        if (rst) begin
            cycle_count <= 16'd0;
            instr_count <= 16'd0;
        end else if (!halted) begin
            cycle_count <= cycle_count + 16'd1;
            instr_count <= instr_count + 16'd1;
        end
    end

    assign dbg_regs = {r7, r6, r5, r4, r3, r2, r1, r0};
endmodule
`default_nettype wire

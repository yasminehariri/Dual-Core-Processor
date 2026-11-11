"""One single-cycle core - Python model of src/core.v.

Contains the same parts as core.v: instruction memory, decoder, control unit,
register file, ALU, PC unit, the 4 datapath muxes and the 2 counters.

A clock cycle is split in two phases, like real hardware:
    1. evaluate(mem_rdata)  - combinational: every wire of core.v is computed
                              from the CURRENT state (nothing is changed)
    2. clock(wires)         - the posedge: registers, PC and counters update
The shared memory sits outside the core (in dual_core.py), connected through
mem_addr / mem_wdata / mem_we / mem_rdata just like the Verilog ports.
"""
from __future__ import annotations

from dataclasses import dataclass

from .alu import ALU
from .control_unit import Control, control
from .decoder import Fields, decode
from .instr_mem import InstructionMemory
from .pc_unit import PCUnit
from .regfile import RegisterFile


@dataclass(frozen=True)
class CoreWires:
    """Every named wire of core.v for one cycle (useful for tracing / debugging)."""
    pc: int
    instr: int
    f: Fields                 # decoder outputs
    ctl: Control              # control unit outputs
    ra2: int                  # Mux 1 output (Reg2 mux)
    rd1: int
    rd2: int
    alu_b: int                # Mux 2 output (ALU-B mux)
    alu_result: int
    zero: int
    carry: int
    overflow: int
    mem_rdata: int
    wb_data: int              # Mux 3 output (WB mux)
    branch_taken: int         # feeds Mux 4 inside pc_unit
    reg_we: int               # reg_write & ~halted
    mem_addr: int
    mem_wdata: int
    mem_we: int               # mem_write & ~halted


class Core:
    """core.v. `imem` plays the role of the PROG parameter."""

    def __init__(self, imem: InstructionMemory) -> None:
        self.imem = imem
        self.rf = RegisterFile()
        self.pcu = PCUnit()
        self.cycle_count: int = 0
        self.instr_count: int = 0

    # ---------------- status outputs ----------------
    @property
    def pc(self) -> int:
        return self.pcu.pc

    @property
    def halted(self) -> int:
        return self.pcu.halted

    def dbg_regs(self) -> list[int]:
        """[R0, ..., R7]  (the Verilog packs them as {R7, ..., R0})."""
        return self.rf.dbg()

    # ---------------- FETCH + MEMORY ADDRESS ----------------
    def instr(self) -> int:
        return self.imem.read(self.pcu.pc)

    @property
    def mem_addr(self) -> int:
        """assign mem_addr = addr8;  depends only on the fetched instruction."""
        return decode(self.instr()).addr8

    # ---------------- PHASE 1: combinational ----------------
    def evaluate(self, mem_rdata: int) -> CoreWires:
        """Compute every wire of core.v from the current state. Changes nothing."""
        pc = self.pcu.pc
        instr = self.imem.read(pc)                                  # FETCH
        f = decode(instr)                                           # DECODE
        ctl = control(f.opcode)
        halted = self.pcu.halted

        ra2 = f.rd if ctl.reg2_sel else f.rt                        # Mux 1: Reg2 mux
        rd1 = self.rf.read(f.rs)                                    # REGISTER READ
        rd2 = self.rf.read(ra2)

        alu_b = f.imm6_sext if ctl.alu_src else rd2                 # Mux 2: ALU-B mux
        alu_result, zero, carry, overflow = ALU.compute(rd1, alu_b, ctl.alu_op)   # EXECUTE

        if ctl.wb_sel == 0b01:                                      # Mux 3: WB mux
            wb_data = mem_rdata & 0xFF
        elif ctl.wb_sel == 0b10:
            wb_data = f.addr8
        else:
            wb_data = alu_result

        branch_taken = ctl.branch & (zero ^ ctl.br_ne)              # BEQ/BNE compare with SUB

        return CoreWires(
            pc=pc, instr=instr, f=f, ctl=ctl, ra2=ra2, rd1=rd1, rd2=rd2, alu_b=alu_b,
            alu_result=alu_result, zero=zero, carry=carry, overflow=overflow,
            mem_rdata=mem_rdata & 0xFF, wb_data=wb_data, branch_taken=branch_taken,
            reg_we=ctl.reg_write & (1 - halted),                    # nothing is written after HALT
            mem_addr=f.addr8, mem_wdata=rd2,                        # STORE data via the Reg2 mux
            mem_we=ctl.mem_write & (1 - halted),
        )

    # ---------------- PHASE 2: posedge clk ----------------
    def clock(self, w: CoreWires, rst: int = 0) -> None:
        """Commit one cycle. Order inside does not matter: everything uses `w`
        (computed before the edge) plus each register's own old value."""
        was_halted = self.pcu.halted

        if rst:
            self.rf.reset()
        else:
            self.rf.write(w.f.rd, w.wb_data, w.reg_we)

        # Mux 4 (next-PC priority) lives inside pc_unit
        self.pcu.clock(rst, w.ctl.halt, w.ctl.jump, w.branch_taken, w.f.addr8, w.f.off6)

        # performance counters: count every cycle not yet halted, INCLUDING the HALT cycle
        if rst:
            self.cycle_count = self.instr_count = 0
        elif not was_halted:
            self.cycle_count = (self.cycle_count + 1) & 0xFFFF
            self.instr_count = (self.instr_count + 1) & 0xFFFF

    def reset(self) -> None:
        """One clock edge with rst = 1."""
        self.clock(self.evaluate(0), rst=1)

"""Pipelining analysis (Module 10): what a classic 5-stage pipeline would do with a program.

No Verilog counterpart and NO change to the simulator: the single-cycle simulator is
run first to get the dynamic instruction sequence (every branch already resolved),
then that sequence is scheduled on IF ID EX MEM WB with these rules:

  * Full forwarding EX/MEM->EX and MEM/WB->EX, for ALU operands, branch operands and STORE data.
  * Load-use: an instruction right after a LOAD that reads the LOAD's Rd (STORE data too)
    waits 1 cycle in ID ("--"), then gets the value by MEM/WB->EX forwarding.
  * BEQ/BNE resolve in EX. Taken: the 2 instructions fetched behind it are flushed (2-cycle penalty).
    Not taken: 0 penalty (we keep fetching PC+1, which was correct).
  * JMP resolves in ID: the 1 instruction fetched behind it is flushed (1-cycle penalty).
  * HALT completes when it leaves WB (pipeline drained). Nothing is fetched after HALT.
  * Register file writes in the first half of a cycle and reads in the second half,
    so a value 3+ instructions back is simply read from the register file.

Cycle count identity:  pipelined = N + 4 (fill/drain) + stall cycles + flushed instructions.

    python -m python_sim.pipeline programs/demo1_core1.asm --data programs/data1.hex \\
                                  --md docs/pipeline_demo1_core1.md
    python -m python_sim.pipeline programs/demo2_core1.asm --data programs/data2.hex \\
                                  --core 1 --other programs/demo2_core0.asm --md docs/pipeline_demo2_core1.md

--core/--other: some programs only finish because the other core does something
(Demo 2's Core 1 spins until Core 0 sets the flag). The program then runs as core
--core next to --other in the normal DualCoreSystem; only the analysed core is scheduled.
"""
from __future__ import annotations

import argparse
import csv
import io
import os
import sys
from dataclasses import dataclass, field
from typing import Optional

from .decoder import decode
from .disasm import disassemble
from .dual_core import DualCoreSystem
from .instr_mem import InstructionMemory
from .run import load_program
from .shared_mem import SharedMemory

STAGES = ("IF", "ID", "EX", "MEM", "WB")
STALL = "--"

OP_LOAD, OP_STORE, OP_LI, OP_ADDI, OP_BEQ, OP_BNE, OP_JMP, OP_HALT = 8, 9, 10, 11, 12, 13, 14, 15


# ---------------------------------------------------------------- dynamic trace
@dataclass(frozen=True)
class Executed:
    """One instruction the single-cycle simulator actually executed."""
    pc: int
    instr: int
    taken: bool          # BEQ/BNE: branch taken (JMP: always True)


def dynamic_trace(imem: InstructionMemory, data: SharedMemory, core: int = 0,
                  other: Optional[InstructionMemory] = None, max_cycles: int = 10_000) -> list[Executed]:
    """Run the existing single-cycle simulator and record what core `core` executes."""
    other = other or InstructionMemory()                    # empty memory = all HALT
    pair = (imem, other) if core == 0 else (other, imem)
    system = DualCoreSystem(pair[0], pair[1], data)
    seq: list[Executed] = []

    def record(rec) -> None:
        w = rec.wires[core]
        if w is not None:
            seq.append(Executed(w.pc, w.instr, bool(w.branch_taken or w.ctl.jump)))

    if not system.run(max_cycles, record):
        raise RuntimeError(f"core {core} did not halt within {max_cycles} cycles "
                           "(does it wait for the other core? use --other)")
    return seq


def sources(instr: int) -> list[int]:
    """Registers an instruction needs in EX (deduplicated, in order)."""
    f = decode(instr)
    if f.opcode <= 7:
        regs = [f.rs, f.rt]
    elif f.opcode == OP_ADDI:
        regs = [f.rs]
    elif f.opcode == OP_STORE:
        regs = [f.rd]                                       # store data, via the Reg2 mux
    elif f.opcode in (OP_BEQ, OP_BNE):
        regs = [f.rd, f.rs]
    else:
        regs = []
    return list(dict.fromkeys(regs))


def dest(instr: int) -> Optional[int]:
    """Register written, or None."""
    f = decode(instr)
    return f.rd if f.opcode <= 7 or f.opcode in (OP_LOAD, OP_LI, OP_ADDI) else None


# ---------------------------------------------------------------- scheduling
@dataclass
class Row:
    """One row of the pipeline diagram."""
    pc: int
    instr: int
    flushed: bool = False
    cells: dict[int, str] = field(default_factory=dict)    # cycle (1-based) -> "IF" / "--" / ...

    def place(self, stage: str, start: int, end: int) -> None:
        """Stage `stage` entered at `start`; the instruction stays (stalled) until `end` - 1."""
        self.cells[start] = stage
        for c in range(start + 1, end):
            self.cells[c] = STALL

    @property
    def text(self) -> str:
        return disassemble(self.instr)


@dataclass
class Schedule:
    rows: list[Row]
    n_instr: int
    cycles: int
    load_use: list[str]          # one entry per stall cycle: "LOAD R2 -> SLL R3, R1, R2"
    branch_flushes: int          # taken BEQ/BNE (each flushes 2)
    jump_flushes: int            # JMP (each flushes 1)
    forwards: list[str]          # "SUB R6, R5, R1 -> STORE R6, [0x41] (EX/MEM->EX, R6)"

    @property
    def stall_cycles(self) -> int:
        return len(self.load_use)

    @property
    def flushed_instructions(self) -> int:
        return 2 * self.branch_flushes + self.jump_flushes

    @property
    def cpi(self) -> float:
        return self.cycles / self.n_instr

    @property
    def speedup(self) -> float:
        """Single-cycle N x T  vs  pipelined cycles x T/5."""
        return 5 * self.n_instr / self.cycles


def schedule(seq: list[Executed], imem: InstructionMemory) -> Schedule:
    """Place every executed instruction (and every flushed wrong-path fetch) in the pipeline.

    For instruction i (prev = i-1), all times are 1-based cycle numbers:
        IF  = ID[prev]           normally (fetched as soon as prev moves on)
            = EX[prev] + 1       if prev is a taken branch (target known at end of EX)
            = ID[prev] + 1       if prev is JMP (target known at end of ID)
        ID  = max(IF + 1, EX[prev])                     wait in IF while prev is stalled in ID
        EX  = max(ID + 1, WB[j] for every LOAD j whose Rd i reads)   load-use stall
        MEM = EX + 1,  WB = MEM + 1
    """
    rows: list[Row] = []
    load_use: list[str] = []
    forwards: list[str] = []
    branch_flushes = jump_flushes = 0
    last_writer: dict[int, tuple[int, Executed, int, int]] = {}   # reg -> (index, instr, EX, WB)
    prev_t: Optional[dict[str, int]] = None
    prev: Optional[Executed] = None

    for i, ex in enumerate(seq):
        op = decode(ex.instr).opcode
        # ---- IF ----
        if prev_t is None:
            t_if = 1
        elif decode(prev.instr).opcode in (OP_BEQ, OP_BNE) and prev.taken:
            t_if = prev_t["EX"] + 1
        elif decode(prev.instr).opcode == OP_JMP:
            t_if = prev_t["ID"] + 1
        else:
            t_if = prev_t["ID"]
        # ---- ID ----
        t_id = max(t_if + 1, prev_t["EX"] if prev_t else 0)
        # ---- EX: load-use ----
        t_ex = t_id + 1
        for r in sources(ex.instr):
            if r in last_writer:
                _, w, w_ex, w_wb = last_writer[r]
                if decode(w.instr).opcode == OP_LOAD and w_wb > t_ex:
                    for _ in range(w_wb - t_ex):
                        load_use.append(f"{disassemble(w.instr)} -> {disassemble(ex.instr)}")
                    t_ex = w_wb
        t = {"IF": t_if, "ID": t_id, "EX": t_ex, "MEM": t_ex + 1, "WB": t_ex + 2}

        # ---- forwarding actually used ----
        for r in sources(ex.instr):
            if r in last_writer:
                _, w, w_ex, w_wb = last_writer[r]
                if t_ex == w_ex + 1:
                    path = "EX/MEM->EX"
                elif t_ex == w_ex + 2:
                    path = "MEM/WB->EX"
                else:
                    continue                                # read from the register file
                forwards.append(f"{disassemble(w.instr)} -> {disassemble(ex.instr)} ({path}, R{r})")

        row = Row(ex.pc, ex.instr)
        row.place("IF", t["IF"], t["ID"])
        row.place("ID", t["ID"], t["EX"])
        for s in ("EX", "MEM", "WB"):
            row.place(s, t[s], t[s] + 1)
        rows.append(row)

        # ---- wrong-path fetches behind a taken branch / jump ----
        if op in (OP_BEQ, OP_BNE) and ex.taken:
            branch_flushes += 1
            w1 = Row((ex.pc + 1) & 0xFF, imem.read(ex.pc + 1), flushed=True)
            w1.place("IF", t["ID"], t["EX"])
            w1.place("ID", t["EX"], t["EX"] + 1)
            w2 = Row((ex.pc + 2) & 0xFF, imem.read(ex.pc + 2), flushed=True)
            w2.place("IF", t["EX"], t["EX"] + 1)
            rows += [w1, w2]
        elif op == OP_JMP:
            jump_flushes += 1
            w1 = Row((ex.pc + 1) & 0xFF, imem.read(ex.pc + 1), flushed=True)
            w1.place("IF", t["ID"], t["ID"] + 1)
            rows.append(w1)

        d = dest(ex.instr)
        if d is not None:
            last_writer[d] = (i, ex, t["EX"], t["WB"])
        prev, prev_t = ex, t
        if op == OP_HALT:
            break

    cycles = prev_t["WB"] if prev_t else 0
    return Schedule(rows, len(seq), cycles, load_use, branch_flushes, jump_flushes, forwards)


def analyse(prog_path: str, data_path: Optional[str], core: int = 0,
            other_path: Optional[str] = None) -> tuple[Schedule, int]:
    """Returns (schedule, single-cycle cycle count from the simulator)."""
    imem = load_program(prog_path)
    other = load_program(other_path) if other_path else None
    seq = dynamic_trace(imem, SharedMemory(data_path), core, other)
    return schedule(seq, imem), len(seq)


# ---------------------------------------------------------------- output
def table(s: Schedule) -> list[list[str]]:
    """Header + one row per instruction: #, PC, instruction, cycle 1..N."""
    head = ["#", "PC", "Instruction"] + [str(c) for c in range(1, s.cycles + 1)]
    out = [head]
    n = 0
    for r in s.rows:
        if r.flushed:
            label, text = "x", f"{r.text} (flushed)"
        else:
            n += 1
            label, text = str(n), r.text
        out.append([label, str(r.pc), text] + [r.cells.get(c, "") for c in range(1, s.cycles + 1)])
    return out


def summary_rows(s: Schedule, single_cycles: int) -> list[tuple[str, str]]:
    single_t, pipe_t = single_cycles, s.cycles / 5
    return [
        ("Instructions executed", str(s.n_instr)),
        ("Single-cycle cycles (clock = T)", f"{single_cycles}  ->  {single_t}T"),
        ("Pipelined cycles (clock = T/5)", f"{s.cycles}  ->  {s.cycles} x 0.2T = {pipe_t:g}T"),
        ("Fill + drain", "4"),
        ("Stalls: load-use", str(s.stall_cycles)),
        ("Flushes: taken BEQ/BNE (2 each)", f"{s.branch_flushes} branches = {2 * s.branch_flushes} instructions"),
        ("Flushes: JMP (1 each)", f"{s.jump_flushes} jumps = {s.jump_flushes} instructions"),
        ("Check: N + 4 + stalls + flushes", f"{s.n_instr} + 4 + {s.stall_cycles} + {s.flushed_instructions} = "
                                            f"{s.n_instr + 4 + s.stall_cycles + s.flushed_instructions}"),
        ("CPI", f"{s.cpi:.3f}"),
        ("Speedup (single-cycle time / pipelined time)", f"{single_t}T / {pipe_t:g}T = {single_t / pipe_t:.2f}x"),
    ]


def to_markdown(s: Schedule, single_cycles: int, title: str, note: str = "") -> str:
    md = io.StringIO()
    md.write(f"# Pipeline analysis: {title}\n\n")
    md.write("Generated by `python_sim/pipeline.py` (5-stage IF ID EX MEM WB, full forwarding, "
             "branches resolved in EX, JMP in ID). `--` = stall, `(flushed)` = wrong-path fetch "
             "squashed by a taken branch or jump.\n\n")
    if note:
        md.write(note + "\n\n")
    md.write("## Summary\n\n| Quantity | Value |\n|---|---|\n")
    for k, v in summary_rows(s, single_cycles):
        md.write(f"| {k} | {v} |\n")
    md.write("\n**Load-use stalls**\n\n")
    md.write("".join(f"- {x}\n" for x in s.load_use) or "- none\n")
    md.write("\n**Forwarding used**\n\n")
    md.write("".join(f"- {x}\n" for x in s.forwards) or "- none\n")
    md.write("\n## Pipeline diagram\n\n")
    t = table(s)
    md.write("| " + " | ".join(t[0]) + " |\n")
    md.write("|" + "---|" * len(t[0]) + "\n")
    for row in t[1:]:
        md.write("| " + " | ".join(row) + " |\n")
    return md.getvalue()


def to_csv(s: Schedule) -> str:
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(table(s))
    return buf.getvalue()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="5-stage pipeline analysis of one core's program")
    ap.add_argument("program", help="program for the analysed core (.hex or .asm)")
    ap.add_argument("--data", help="shared memory init file (.hex)")
    ap.add_argument("--core", type=int, choices=(0, 1), default=0, help="which core runs the program (default 0)")
    ap.add_argument("--other", help="program for the other core (default: just HALT)")
    ap.add_argument("--md", help="write the Markdown report here")
    ap.add_argument("--csv", help="write the diagram as CSV here (default: next to --md)")
    args = ap.parse_args(argv)

    s, single = analyse(args.program, args.data, args.core, args.other)
    title = os.path.splitext(os.path.basename(args.program))[0]
    note = ""
    if args.other:
        note = (f"Dynamic sequence from the single-cycle dual-core run, this program on core {args.core} next to "
                f"`{os.path.basename(args.other)}`. The number of spin-loop iterations depends on the other core's "
                "timing, so it is the single-cycle count; a pipelined system would spin a different number of times.")
    md = to_markdown(s, single, title, note)

    for k, v in summary_rows(s, single):
        print(f"{k:46s} {v}")
    if args.md:
        os.makedirs(os.path.dirname(os.path.abspath(args.md)), exist_ok=True)
        with open(args.md, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"wrote {args.md}")
    csv_path = args.csv or (os.path.splitext(args.md)[0] + ".csv" if args.md else None)
    if csv_path:
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            f.write(to_csv(s))
        print(f"wrote {csv_path}")
    if not args.md:
        print()
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())

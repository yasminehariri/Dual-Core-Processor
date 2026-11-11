"""Command-line runner for the dual-core simulator (no Verilog counterpart; plays the testbench role).

From the repo root:
    python -m python_sim.run --prog0 programs/demo1_core0.hex --prog1 programs/demo1_core1.hex \\
                             --data programs/data1.hex [--trace] [--max-cycles 1000]

--prog0 / --prog1 also accept .asm files; they are assembled with tools/asm.py
(in memory - no .hex file is written).
"""
from __future__ import annotations

import argparse
import os
import sys

from .disasm import disassemble
from .dual_core import CycleRecord, DualCoreSystem
from .instr_mem import InstructionMemory
from .shared_mem import SharedMemory

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_program(path: str) -> InstructionMemory:
    """A .hex file is loaded like $readmemh; a .asm file is assembled with tools/asm.py first."""
    if not path.lower().endswith(".asm"):
        return InstructionMemory(path)
    sys.path.insert(0, os.path.join(REPO, "tools"))
    try:
        from asm import AsmError, assemble_text
    finally:
        sys.path.pop(0)
    with open(path, encoding="utf-8") as f:
        try:
            words, warnings, _ = assemble_text(f.read())
        except AsmError as e:
            raise SystemExit(f"error: {path}: {e}")
    for w in warnings:
        print(f"warning: {path}: {w}", file=sys.stderr)
    return InstructionMemory(words=words)


def print_trace(rec: CycleRecord) -> None:
    for i, w in enumerate(rec.wires):
        if w is not None:                     # a halted core executes nothing
            print(f"cycle {rec.cycle:4d}  core{i}  pc {w.pc:3d}  {w.instr:04X}  {disassemble(w.instr, w.pc)}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Cycle-accurate simulator of the CCEE 324 dual-core processor")
    ap.add_argument("--prog0", required=True, help="Core 0 program (.hex or .asm)")
    ap.add_argument("--prog1", required=True, help="Core 1 program (.hex or .asm)")
    ap.add_argument("--data", help="shared memory init file (.hex); omitted = all zeros")
    ap.add_argument("--trace", action="store_true", help="print every executed instruction")
    ap.add_argument("--max-cycles", type=int, default=1000, help="stop if not both halted by then (default 1000)")
    args = ap.parse_args(argv)

    system = DualCoreSystem(load_program(args.prog0), load_program(args.prog1), SharedMemory(args.data))
    finished = system.run(args.max_cycles, print_trace if args.trace else None)
    if args.trace:
        print()

    for i, core in enumerate(system.cores):
        regs = "  ".join(f"R{r}={v:02X}" for r, v in enumerate(core.dbg_regs()))
        print(f"core{i}  {regs}")
    nz = system.mem.nonzero()
    print("memory (non-zero): " + ("  ".join(f"[{a:02X}]={v:02X}" for a, v in nz.items()) or "all zero"))
    c0, c1 = system.core0.cycle_count, system.core1.cycle_count
    print(f"core0 cycles = {c0}   core1 cycles = {c1}")
    print(f"dual-core time = max(C0, C1) = {system.dual_core_time()}")
    if not finished:
        print(f"WARNING: not both halted after {args.max_cycles} cycles", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

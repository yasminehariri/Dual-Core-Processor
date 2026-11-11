"""Generate docs/report_data.md: the tables that go into the report (no Verilog counterpart).

    python -m python_sim.report_data                # writes docs/report_data.md
    python -m python_sim.report_data --out other.md

Everything is computed: cycle tables come from the simulator, the Demo 3 breakdown
from Core 1's trace, the Verilog check counts from logs/*.log (Questa or Icarus),
and the Python counts from actually running the test suites.
"""
from __future__ import annotations

import argparse
import glob
import io
import os
import re
import sys
import unittest
from dataclasses import dataclass
from fractions import Fraction

from .decoder import decode
from .disasm import disassemble
from .dual_core import DualCoreSystem

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda name: os.path.join(REPO, "programs", name)          # noqa: E731

DEMOS = {
    "demo1": ("demo1_core0.hex", "demo1_core1.hex", "data1.hex"),
    "demo2": ("demo2_core0.hex", "demo2_core1.hex", "data2.hex"),
    "demo3": ("demo3_core0.hex", "demo3_core1.hex", "data3.hex"),
    "single": ("demo3_single.hex", "halt.hex", "data3.hex"),
}
FLAG_ADDR = 0xF0
OP_LOAD = 8


# ---------------------------------------------------------------- cycle tables
@dataclass
class Run:
    system: DualCoreSystem
    rows: list[tuple]           # (cycle, (pc, instr) | None, (pc, instr) | None, [memory writes])


def run_demo(name: str) -> Run:
    p0, p1, data = DEMOS[name]
    s = DualCoreSystem.from_files(P(p0), P(p1), P(data))
    rows: list[tuple] = []

    def rec(r) -> None:
        cells, writes = [], []
        for i, w in enumerate(r.wires):
            cells.append(None if w is None else (w.pc, w.instr))
            if w is not None and w.mem_we:
                writes.append(f"core{i}: Mem[{w.mem_addr:02X}] <- {w.mem_wdata:02X}")
        rows.append((r.cycle, cells[0], cells[1], writes))

    assert s.run(1000, rec), f"{name} did not halt"
    return Run(s, rows)


def cycle_table(run: Run) -> str:
    out = io.StringIO()
    out.write("| Cycle | Core 0 PC | Core 0 instruction | Core 1 PC | Core 1 instruction | Shared-memory write |\n")
    out.write("|---|---|---|---|---|---|\n")
    for cycle, c0, c1, writes in run.rows:
        def cell(c):
            return ("-", "(halted)") if c is None else (str(c[0]), f"`{c[1]:04X}` {disassemble(c[1])}")
        a, b = cell(c0), cell(c1)
        out.write(f"| {cycle} | {a[0]} | {a[1]} | {b[0]} | {b[1]} | {'; '.join(writes) or ''} |\n")
    s = run.system
    out.write(f"\nCore 0: {s.core0.cycle_count} cycles. Core 1: {s.core1.cycle_count} cycles. "
              f"T_dual = max(C0, C1) = {s.dual_core_time()}.\n")
    return out.getvalue()


# ---------------------------------------------------------------- Demo 3 breakdown
def core1_breakdown(run: Run) -> tuple[int, int, int]:
    """Split Core 1's cycles into (parallel work, waiting on the flag, combining).

    Waiting = from the first LOAD of the flag address through the branch that
    finally falls through; parallel = everything before; combining = everything after.
    """
    executed = [c1 for _, _, c1, _ in run.rows if c1 is not None]
    first = next(i for i, (_, ins) in enumerate(executed)
                 if decode(ins).opcode == OP_LOAD and decode(ins).addr8 == FLAG_ADDR)
    loop_pcs = {executed[first][0], executed[first + 1][0]}          # LOAD flag + BEQ
    last = max(i for i, (pc, _) in enumerate(executed) if pc in loop_pcs)
    parallel, waiting = first, last - first + 1
    return parallel, waiting, len(executed) - parallel - waiting


def demo3_summary(dual: Run, single: Run) -> str:
    c0, c1 = dual.system.core0.cycle_count, dual.system.core1.cycle_count
    t_single = single.system.core0.cycle_count
    t_dual = dual.system.dual_core_time()
    par, wait, comb = core1_breakdown(dual)
    s = Fraction(t_single, t_dual)
    f = 2 / s - 1                                          # from S = 1 / (f + (1 - f) / 2)
    out = io.StringIO()
    out.write("| Core 1 phase | Cycles |\n|---|---|\n")
    out.write(f"| Parallel work (sum of 9..16) | {par} |\n")
    out.write(f"| Waiting on the flag (spin loop) | {wait} |\n")
    out.write(f"| Combining (load partial, add, store, halt) | {comb} |\n")
    out.write(f"| **Total** | **{par + wait + comb}** |\n\n")
    out.write("| Quantity | Value |\n|---|---|\n")
    out.write(f"| Single core T_single | {t_single} cycles |\n")
    out.write(f"| Core 0 / Core 1 | {c0} / {c1} cycles |\n")
    out.write(f"| T_dual = max(C0, C1) | max({c0}, {c1}) = {t_dual} cycles |\n")
    out.write(f"| Speedup S = T_single / T_dual | {t_single}/{t_dual} = {float(s):.2f} |\n")
    out.write(f"| Amdahl-equivalent serial fraction f = 2/S - 1 | 2 x {t_dual}/{t_single} - 1 = "
              f"{f.numerator}/{f.denominator} = {float(f) * 100:.1f}% |\n")
    return out.getvalue()


# ---------------------------------------------------------------- test summary
VERILOG_TBS = [
    ("tb_hello", "install check (clock)"),
    ("tb_alu", "ALU: 26 cases x (result, Z, C, V)"),
    ("tb_regfile", "register file"),
    ("tb_control_unit", "control unit, 16 opcodes + decoder fields"),
    ("tb_pc_unit", "PC unit"),
    ("tb_instr_mem", "instruction memory"),
    ("tb_shared_mem", "shared memory incl. write conflict"),
    ("tb_core", "single core: core_all + loop_test"),
    ("tb_dual_core", "Demos 1-3, single core, conflict"),
]


def verilog_counts() -> list[tuple[str, str, str, str]]:
    rows = []
    for name, what in VERILOG_TBS:
        path = os.path.join(REPO, "logs", f"{name}.log")
        if not os.path.exists(path):
            rows.append((name, what, "?", "no log (run `do run_all.do`)"))
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        m = re.search(r"ALL PASS \((\d+) checks\)", text)
        if m:
            rows.append((name, what, m[1], "ALL PASS"))
        else:
            m = re.search(r"FAILED (\d+) of (\d+)", text)
            rows.append((name, what, m[2] if m else "?", f"FAILED {m[1]}" if m else "no summary line"))
    return rows


class _Counting(unittest.TestResult):
    """Counts tests and subtests per test file."""

    def __init__(self) -> None:
        super().__init__()
        self.per_file: dict[str, list[int]] = {}       # file -> [tests, subtests]

    def _key(self, test) -> str:
        return test.__class__.__module__.split(".")[-1]

    def startTest(self, test) -> None:
        super().startTest(test)
        self.per_file.setdefault(self._key(test), [0, 0])[0] += 1

    def addSubTest(self, test, subtest, err) -> None:
        super().addSubTest(test, subtest, err)
        self.per_file.setdefault(self._key(test), [0, 0])[1] += 1


def python_counts() -> tuple[list[tuple[str, int, int]], _Counting, _Counting]:
    loader = unittest.TestLoader()
    sim = _Counting()
    loader.discover(os.path.join(REPO, "python_sim", "tests"), top_level_dir=REPO).run(sim)
    asm = _Counting()
    sys.path.insert(0, os.path.join(REPO, "tools"))
    try:
        loader.loadTestsFromName("test_asm").run(asm)
    finally:
        sys.path.pop(0)
    rows = [(f"python_sim/tests/{k}.py", v[0], v[1]) for k, v in sorted(sim.per_file.items())]
    rows += [("tools/test_asm.py", v[0], v[1]) for v in asm.per_file.values()]
    return rows, sim, asm


def test_summary() -> str:
    out = io.StringIO()
    out.write("**Verilog testbenches** (counts from `logs/*.log`)\n\n")
    out.write("| Testbench | Covers | Checks | Result |\n|---|---|---|---|\n")
    total = 0
    for name, what, n, res in verilog_counts():
        out.write(f"| {name} | {what} | {n} | {res} |\n")
        total += int(n) if n.isdigit() else 0
    out.write(f"| **Total** | | **{total}** | |\n\n")

    rows, sim, asm = python_counts()
    out.write("**Python tests** (run while generating this file)\n\n")
    out.write("| Test file | Tests | Subtests | Result |\n|---|---|---|---|\n")
    ok = {True: "OK", False: "FAILED"}
    for name, t, st in rows:
        good = (asm if name.startswith("tools") else sim).wasSuccessful()
        out.write(f"| {name} | {t} | {st} | {ok[good]} |\n")
    tt, ts = sum(r[1] for r in rows), sum(r[2] for r in rows)
    out.write(f"| **Total** | **{tt}** | **{ts}** | |\n\n")
    out.write("The ALU test also sweeps all 8 x 256 x 256 = 524,288 input combinations inside one test.\n")
    return out.getvalue()


# ---------------------------------------------------------------- main
def build() -> str:
    runs = {k: run_demo(k) for k in DEMOS}
    md = io.StringIO()
    md.write("# Report data\n\nGenerated by `python -m python_sim.report_data`. Do not edit by hand.\n\n")
    md.write("## Demo 3: parallel sum of 1..16\n\n")
    md.write(demo3_summary(runs["demo3"], runs["single"]) + "\n")
    md.write("### Demo 3 cycle table\n\n" + cycle_table(runs["demo3"]) + "\n")
    md.write("## Demo 1: independent cores + shared memory\n\n" + cycle_table(runs["demo1"]) + "\n")
    md.write("## Demo 2: flag synchronization\n\n" + cycle_table(runs["demo2"]) + "\n")
    md.write("## Test summary\n\n" + test_summary())
    return md.getvalue()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate the report tables")
    ap.add_argument("--out", default=os.path.join(REPO, "docs", "report_data.md"))
    args = ap.parse_args(argv)
    text = build()
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

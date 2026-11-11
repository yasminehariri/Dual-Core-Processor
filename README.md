# CCEE 324 Dual-Core Processor

[![tests](https://github.com/yasminehariri/Dual-Core-Processor/actions/workflows/tests.yml/badge.svg)](https://github.com/yasminehariri/Dual-Core-Processor/actions/workflows/tests.yml)

An 8-bit dual-core processor in Verilog: two single-cycle cores, each with its own PC,
instruction memory, decoder, control unit, register file and ALU, sharing one 256 x 8
dual-port data memory. 16 instructions (11 required + 5 bonus).

**Team:** Yasmine (RTL), Reina (verification), Rand (toolchain and docs)
**Spec:** `CCEE324_Dual_Core_Scope_v2.3.docx` (single source of truth)
**Tools:** Quartus Prime Lite 21.1 + Questa-Intel FPGA Starter Edition, Python 3

## Status (8 Nov 2026)

All Tier A hardware is built and verified in simulation:

| Testbench | Checks | Result |
|---|---|---|
| tb_alu | 104 | ALL PASS |
| tb_regfile | 23 | ALL PASS |
| tb_control_unit (+ decoder) | 25 | ALL PASS |
| tb_pc_unit | 17 | ALL PASS |
| tb_instr_mem | 19 | ALL PASS |
| tb_shared_mem | 11 | ALL PASS |
| tb_core | 24 | ALL PASS |
| tb_dual_core (Demos 1-3 + conflict) | 25 | ALL PASS |
| tools/test_asm.py | 15 tests | OK |
| python_sim tests | 26 | OK |
| Verilog vs Python | all demos identical | see python_sim/COMPARISON.md |

Demo 3: single core 33 cycles, dual core 25 cycles, speedup 1.32x.

## Folders

| Folder | Contents |
|---|---|
| `src/` | Design modules (Verilog-2001, synthesizable). One module per file. |
| `tb/` | Self-checking testbenches. File name = module name (`tb_alu.v` holds `module tb_alu`). |
| `programs/` | Assembly programs (`.asm`) and assembled `.hex` files |
| `tools/` | `asm.py` assembler and its tests |
| `python_sim/` | Cycle-accurate Python simulator (one class per Verilog module), its tests, pipeline analysis, report-data generator |
| `quartus/` | Quartus project (`ccee324_dual_core.qpf`) |
| `docs/` | Report, diagrams, `waves/` (one `.vcd` per testbench), `bug_list.md`, `pipeline_*.md/.csv`, `report_data.md` (generated) |
| `.github/workflows/` | CI: assembler + Python tests, all testbenches on Icarus Verilog, Verilog-vs-Python trace check |

## Quartus (daily compile check and RTL Viewer)

1. Open `quartus/ccee324_dual_core.qpf`.
2. Processing > Start > **Start Analysis & Elaboration**. Must finish with 0 errors.
3. Tools > Netlist Viewers > **RTL Viewer** to see the circuit.

## Questa (simulation) - always from the repo root

Open Questa, then in its Transcript window:

```
cd C:/path/to/Dual-Core-Processor
do run_all.do                      # runs every testbench, prints ALL PASS / FAILED
```

One testbench with waveforms:

```
vlib work
vlog src/*.v tb/tb_top_smoke.v
vsim -onfinish stop tb_top_smoke
add wave -r /*
run -all
```

`-onfinish stop` keeps Questa open at the end of the test instead of asking "Are you sure you want to finish?".

Do **not** start simulations from Quartus's "Run Simulation Tool" menu: it runs Questa
inside `quartus/simulation/questa`, where the `programs/*.hex` paths do not resolve.

## Programs

| File | What it is |
|---|---|
| `demo1_core0/1.asm` + `data1.hex` | Demo 1: independent cores, Core 1 reads Core 0's result |
| `demo2_core0/1.asm` | Demo 2: flag synchronization (spin-wait on 0xF0) |
| `demo3_core0/1.asm`, `demo3_single.asm` + `data3.hex` | Demo 3: parallel sum of 1..16 |
| `conflict_core0/1.asm` | Both cores store to 0x50 in the same cycle |
| `core_all.asm`, `loop_test.asm` | Used by tb_core |
| `test_encodings.asm` | The 16 reference encodings (used by tb_instr_mem) |
| `core0.hex`, `core1.hex`, `data.hex` | What Quartus loads (copies of Demo 1) |

Assemble after editing a program: `python tools/asm.py programs/<name>.asm -l`
(`-l` prints a listing: instruction number, hex, source).

## Python simulator (`python_sim/`)

A cycle-accurate Python model of the same processor, used as independent verification
of the RTL (results: [python_sim/COMPARISON.md](python_sim/COMPARISON.md)).
Python 3.10+, standard library only. Run everything from the repo root.

```
python -m python_sim.run --prog0 programs/demo1_core0.hex --prog1 programs/demo1_core1.hex --data programs/data1.hex
python -m python_sim.run --prog0 programs/demo2_core0.asm --prog1 programs/demo2_core1.asm --data programs/data2.hex --trace
python -m unittest discover -s python_sim/tests -t .      # or: python -m pytest python_sim/tests
```

Options: `--trace` prints every executed instruction (cycle, core, pc, hex, disassembly);
`--max-cycles N` (default 1000). `.asm` files are assembled in memory with `tools/asm.py`.
Output: R0-R7 of both cores, non-zero memory bytes, cycle counts, and `dual-core time = max(C0, C1)`.

| Python file | Verilog module | Notes |
|---|---|---|
| `alu.py` | `alu.v` | `ALU.compute(a, b, alu_op) -> (result, zero, carry, overflow)`, one 9-bit adder for ADD/SUB |
| `regfile.py` | `regfile.v` | `read()` combinational, `write()` = the clock edge |
| `decoder.py` | `decoder.v` | `decode(instr)` returns the 7 output fields |
| `control_unit.py` | `control_unit.v` | `control(opcode)` returns the 11 signals; `.bits()` packs the 14 bits |
| `pc_unit.py` | `pc_unit.v` | next-PC priority: reset > halt > jump > branch > PC+1 |
| `instr_mem.py` | `instr_mem.v` | 256 x 16, unused words = HALT (F000) |
| `shared_mem.py` | `shared_mem.v` | 256 x 8, Core 1 written first so Core 0 wins conflicts |
| `core.py` | `core.v` | same 4 muxes and 2 counters; `evaluate()` = combinational, `clock()` = posedge |
| `dual_core.py` | `dual_core_top.v` | both cores evaluate from the current state, then all writes commit together |
| `hexfile.py`, `disasm.py`, `run.py` | - | `$readmemh` reader, disassembler, CLI |

Tests in `python_sim/tests/` mirror `tb/` one to one (`test_alu.py` <-> `tb_alu.v`, ...).
If `logs/tb_core.log` and `logs/tb_dual_core.log` exist (from `do run_all.do`), the tests
also compare the Python cycle-by-cycle trace with Questa's, line for line.

**Pipelining analysis (Module 10).** `python_sim/pipeline.py` takes the instruction sequence the
simulator actually executed and schedules it on a 5-stage pipeline (full forwarding, load-use = 1 stall,
taken branch = 2 flushed, JMP = 1 flushed), printing a diagram (Markdown + CSV) and CPI / speedup:

```
python -m python_sim.pipeline programs/demo1_core1.asm --data programs/data1.hex --md docs/pipeline_demo1_core1.md
python -m python_sim.pipeline programs/demo2_core1.asm --data programs/data2.hex --core 1 --other programs/demo2_core0.asm --md docs/pipeline_demo2_core1.md
python -m python_sim.pipeline programs/loop_test.asm --data programs/data2.hex --md docs/pipeline_loop_test.md
```

`--core 1 --other ...` runs the program next to a partner core; Demo 2's Core 1 needs it, because
it spins until Core 0 sets the flag.

**Report tables.** `python -m python_sim.report_data` regenerates `docs/report_data.md` (cycle tables
of Demos 1-3, the Demo 3 breakdown and speedup, and a test-summary table read from `logs/` and from
running the Python tests).

## Rules

- Never push failing code to `main`; work on a branch and open a pull request.
- `vlog -lint` clean; Quartus 0 errors and no latch / width / unconnected-port warnings.
- No `#` delays or `$display` in `src/` (testbenches only).
- Commit messages like `alu: add overflow flag`.

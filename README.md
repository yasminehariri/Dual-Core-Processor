# CCEE 324 Dual-Core Processor

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

Demo 3: single core 33 cycles, dual core 25 cycles, speedup 1.32x.

## Folders

| Folder | Contents |
|---|---|
| `src/` | Design modules (Verilog-2001, synthesizable). One module per file. |
| `tb/` | Self-checking testbenches. File name = module name (`tb_alu.v` holds `module tb_alu`). |
| `programs/` | Assembly programs (`.asm`) and assembled `.hex` files |
| `tools/` | `asm.py` assembler and its tests |
| `quartus/` | Quartus project (`ccee324_dual_core.qpf`) |
| `docs/` | Report, diagrams, `waves/` (one `.vcd` per testbench), `bug_list.md` |

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

## Rules

- Never push failing code to `main`; work on a branch and open a pull request.
- `vlog -lint` clean; Quartus 0 errors and no latch / width / unconnected-port warnings.
- No `#` delays or `$display` in `src/` (testbenches only).
- Commit messages like `alu: add overflow flag`.

# CCEE 324 Dual-Core Processor

An 8-bit dual-core processor in Verilog: two single-cycle cores, each with its own PC,
instruction memory, decoder, control unit, register file and ALU, sharing one 256 x 8
dual-port data memory. 16 instructions (11 required + 5 bonus).

**Team:** Yasmine (RTL), Reina (verification), Rand (toolchain and docs)
**Spec:** `CCEE324_Dual_Core_Scope_v2.3.docx` (single source of truth)
**Tools:** Quartus Prime Lite 21.1 + Questa-Intel FPGA Starter Edition, Python 3

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

## Rules

- Never push failing code to `main`; work on a branch and open a pull request.
- `vlog -lint` clean; Quartus 0 errors and no latch / width / unconnected-port warnings.
- No `#` delays or `$display` in `src/` (testbenches only).
- Commit messages like `alu: add overflow flag`.

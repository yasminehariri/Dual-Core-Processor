# Verilog vs Python simulator: independent verification

The Python simulator in `python_sim/` was written from the same specification as the
Verilog in `src/`, with one Python class per Verilog module. Both run the same `.hex`
files. This table compares every result the Verilog testbenches check.

**How each column was obtained**

- **Verilog (Questa):** value checked by `tb/tb_core.v` and `tb/tb_dual_core.v`. Every
  check printed `PASS` (`ALL PASS (24 checks)` and `ALL PASS (25 checks)` in `logs/`), so
  the RTL produced exactly these values.
- **Python:** value produced by `python -m python_sim.run ...` and checked by
  `python_sim/tests/` (all passing).

## Demo 1: independent cores + shared memory (`demo1_core0/1.hex`, `data1.hex`)

| Quantity | Verilog | Python | Match |
|---|---|---|---|
| Core 0 R1 / R2 / R3 | 0C / 05 / 11 | 0C / 05 / 11 | yes |
| Core 1 R1 / R2 / R3 | 05 / 03 / 28 | 05 / 03 / 28 | yes |
| Core 1 R4 / R5 / R6 | 06 / 11 / 0C | 06 / 11 / 0C | yes |
| Mem[0x40] / Mem[0x41] | 11 / 0C | 11 / 0C | yes |
| Core 0 / Core 1 cycles | 5 / 8 | 5 / 8 | yes |

## Demo 2: flag synchronization (`demo2_core0/1.hex`, `data2.hex`)

| Quantity | Verilog | Python | Match |
|---|---|---|---|
| Mem[0x80] result | 2A | 2A | yes |
| Mem[0xF0] flag | 01 | 01 | yes |
| Mem[0x81] | 28 | 28 | yes |
| Core 0 / Core 1 cycles | 7 / 13 | 7 / 13 | yes |
| Core 1 reads flag at cycles | 0, 2, 4, 6 (set at 6) | 0, 2, 4, 6 (set at 6) | yes |
| Core 1 trace (cycle, pc, Mem[F0]), 13 lines | `logs/tb_dual_core.log` | same 13 lines | yes, line for line |

## Demo 3: parallel sum of 1..16 (`data3.hex`)

| Quantity | Verilog | Python | Match |
|---|---|---|---|
| Dual: Mem[0x80] partial sum | 24 (36) | 24 (36) | yes |
| Dual: Mem[0x82] total | 88 (136) | 88 (136) | yes |
| Dual: Core 0 / Core 1 cycles | 19 / 25 | 19 / 25 | yes |
| Single (`demo3_single` + `halt`): Mem[0x82] | 88 | 88 | yes |
| Single: Core 0 cycles | 33 | 33 | yes |
| Dual-core time = max(C0, C1) | 25 | 25 | yes |
| Speedup 33 / 25 | 1.32x | 1.32x | yes |

## Write conflict (`conflict_core0/1.hex`)

| Quantity | Verilog | Python | Match |
|---|---|---|---|
| Mem[0x50] (Core 0 writes AA, Core 1 writes 55, same cycle) | AA | AA | yes |

## Single-core integration (`tb_core.v`)

| Quantity | Verilog | Python | Match |
|---|---|---|---|
| `core_all`: R0..R7 | 00 00 06 02 00 77 2F D0 | 00 00 06 02 00 77 2F D0 | yes |
| `core_all`: Mem[0x20..0x27] | 11 F2 14 03 2F D0 77 06 | 11 F2 14 03 2F D0 77 06 | yes |
| `core_all`: cycles = instructions | 43 | 43 | yes |
| `core_all`: PC after HALT (and 3 cycles later) | 39 | 39 | yes |
| `core_all`: trace (cycle, pc, instr), 43 lines | `logs/tb_core.log` | same 43 lines | yes, line for line |
| `loop_test`: Mem[0x90] / R2 / cycles | 0F / 0F / 19 | 0F / 0F / 19 | yes |

## Unit level

| Module | Verilog testbench | Python test | Result |
|---|---|---|---|
| ALU | `tb_alu.v`, 26 cases (104 checks) | same 26 cases + all 8 x 256 x 256 = 524,288 input combinations against an independent reference | identical |
| Control unit + decoder | `tb_control_unit.v`, 16 opcodes + 6 fields | same | identical |
| PC unit | `tb_pc_unit.v`, 17 checks | same stimulus sequence | identical |
| Register file | `tb_regfile.v`, 23 checks | same | identical |
| Instruction memory | `tb_instr_mem.v`, 19 checks | same | identical |
| Shared memory | `tb_shared_mem.v`, 11 checks | same | identical |

**Conclusion:** two independent models of the processor (RTL in Questa, and a Python
simulator) agree on every register, every memory byte, every cycle count and, where
the testbenches print one, every line of the cycle-by-cycle trace.

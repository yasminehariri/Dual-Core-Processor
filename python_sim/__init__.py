"""Cycle-accurate Python simulator of the CCEE 324 8-bit dual-core processor.

One Python module per Verilog module in src/:

    alu.py           -> src/alu.v
    regfile.py       -> src/regfile.v
    decoder.py       -> src/decoder.v
    control_unit.py  -> src/control_unit.v
    pc_unit.py       -> src/pc_unit.v
    instr_mem.py     -> src/instr_mem.v
    shared_mem.py    -> src/shared_mem.v
    core.py          -> src/core.v
    dual_core.py     -> src/dual_core_top.v

Helpers with no Verilog counterpart: hexfile.py ($readmemh), disasm.py (trace), run.py (CLI).
"""

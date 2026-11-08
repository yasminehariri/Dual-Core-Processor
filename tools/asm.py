#!/usr/bin/env python3
"""
asm.py - assembler for the CCEE 324 dual-core processor (Scope v2.3, Sections 11 and 12).

Usage:
    python tools/asm.py programs/demo1_core0.asm -o programs/demo1_core0.hex
    python tools/asm.py programs/demo1_core0.asm -l        # also print a listing

Input syntax (one instruction per line, case-insensitive):
    ; comment                      everything after ';' is ignored
    loop:                          a label on its own line ...
    wait: LOAD R1, [0xF0]          ... or before an instruction
    ADD  R3, R1, R2                R-type: ADD SUB AND OR XOR NOR SLL SRL
    ADDI R1, R1, -1                I-type: imm6 = -32 .. 31
    LOAD R1, [0x20]                M-type: address 0 .. 255 (brackets optional)
    STORE R3, [0x40]
    LI   R1, 25                    imm8 = 0 .. 255
    BEQ  R1, R0, wait              B-type: label or signed offset -32 .. 31 (relative to PC + 1)
    BNE  R1, R2, loop
    JMP  loop                      J-type: label or instruction number 0 .. 255
    HALT
    NOP | MOV Rd, Rs | NOT Rd, Rs | CLR Rd      pseudo-instructions

Output: one 4-digit hex word per line, the format Verilog's $readmemh reads.
"""
import argparse
import re
import sys

OPCODES = {"ADD": 0x0, "SUB": 0x1, "AND": 0x2, "OR": 0x3, "XOR": 0x4, "NOR": 0x5, "SLL": 0x6, "SRL": 0x7,
           "LOAD": 0x8, "STORE": 0x9, "LI": 0xA, "ADDI": 0xB, "BEQ": 0xC, "BNE": 0xD, "JMP": 0xE, "HALT": 0xF}
R_TYPE = {"ADD", "SUB", "AND", "OR", "XOR", "NOR", "SLL", "SRL"}
WRITES_RD = R_TYPE | {"LOAD", "LI", "ADDI"}
MAX_WORDS = 256


class AsmError(Exception):
    """An error in the source program; the message names the line."""


def _reg(tok, line_no):
    m = re.fullmatch(r"[Rr]([0-9]+)", tok.strip())
    if not m or int(m.group(1)) > 7:
        raise AsmError(f"line {line_no}: '{tok}' is not a register (use R0 to R7)")
    return int(m.group(1))


def _num(tok, line_no, what):
    t = tok.strip().strip("[]").strip()
    try:
        return int(t, 0)
    except ValueError:
        raise AsmError(f"line {line_no}: '{tok}' is not a valid {what}")


def _check_range(v, lo, hi, line_no, what):
    if not lo <= v <= hi:
        raise AsmError(f"line {line_no}: {what} {v} is out of range ({lo} to {hi})")
    return v


def _parse(text):
    """First pass: strip comments, collect labels, return [(line_no, pc, mnemonic, operands, source)]."""
    labels, items, pc = {}, [], 0
    for line_no, raw in enumerate(text.splitlines(), start=1):
        code = raw.split(";", 1)[0].strip()
        while True:                                   # one or more 'label:' prefixes
            m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$", code)
            if not m:
                break
            name = m.group(1).lower()
            if name in labels:
                raise AsmError(f"line {line_no}: label '{m.group(1)}' is defined twice")
            if name.upper() in OPCODES or re.fullmatch(r"r[0-9]+", name):
                raise AsmError(f"line {line_no}: '{m.group(1)}' cannot be used as a label name")
            labels[name] = pc
            code = m.group(2).strip()
        if not code:
            continue
        parts = code.split(None, 1)
        mnem = parts[0].upper()
        ops = [o.strip() for o in parts[1].split(",")] if len(parts) > 1 else []
        items.append((line_no, pc, mnem, ops, raw.strip()))
        pc += 1
    if pc > MAX_WORDS:
        raise AsmError(f"program has {pc} instructions; the instruction memory holds {MAX_WORDS}")
    return labels, items


def _expect(ops, n, line_no, mnem, form):
    if len(ops) != n:
        raise AsmError(f"line {line_no}: {mnem} takes {n} operand(s): {form}")


def assemble_text(text):
    """Assemble source text. Returns (words, warnings, listing). Raises AsmError."""
    labels, items = _parse(text)
    words, warnings, listing = [], [], []
    for line_no, pc, mnem, ops, src in items:
        pseudo = None
        if mnem == "NOP":
            _expect(ops, 0, line_no, mnem, "NOP")
            pseudo, mnem, ops = "NOP", "OR", ["R0", "R0", "R0"]
        elif mnem == "MOV":
            _expect(ops, 2, line_no, mnem, "MOV Rd, Rs")
            pseudo, mnem, ops = "MOV", "OR", [ops[0], ops[1], ops[1]]
        elif mnem == "NOT":
            _expect(ops, 2, line_no, mnem, "NOT Rd, Rs")
            pseudo, mnem, ops = "NOT", "NOR", [ops[0], ops[1], ops[1]]
        elif mnem == "CLR":
            _expect(ops, 1, line_no, mnem, "CLR Rd")
            pseudo, mnem, ops = "CLR", "XOR", [ops[0], ops[0], ops[0]]

        if mnem not in OPCODES:
            raise AsmError(f"line {line_no}: unknown instruction '{mnem}'")
        op = OPCODES[mnem]

        if mnem in R_TYPE:
            _expect(ops, 3, line_no, mnem, f"{mnem} Rd, Rs, Rt")
            rd, rs, rt = (_reg(o, line_no) for o in ops)
            word = (op << 12) | (rd << 9) | (rs << 6) | (rt << 3)
        elif mnem == "ADDI":
            _expect(ops, 3, line_no, mnem, "ADDI Rd, Rs, imm6")
            rd, rs = _reg(ops[0], line_no), _reg(ops[1], line_no)
            imm = _check_range(_num(ops[2], line_no, "immediate"), -32, 31, line_no, "ADDI immediate")
            word = (op << 12) | (rd << 9) | (rs << 6) | (imm & 0x3F)
        elif mnem in ("LOAD", "STORE"):
            _expect(ops, 2, line_no, mnem, f"{mnem} R, [addr]")
            r = _reg(ops[0], line_no)
            addr = _check_range(_num(ops[1], line_no, "address"), 0, 255, line_no, "address")
            word = (op << 12) | (r << 9) | addr
        elif mnem == "LI":
            _expect(ops, 2, line_no, mnem, "LI Rd, imm8")
            r = _reg(ops[0], line_no)
            imm = _check_range(_num(ops[1], line_no, "immediate"), 0, 255, line_no, "LI immediate")
            word = (op << 12) | (r << 9) | imm
        elif mnem in ("BEQ", "BNE"):
            _expect(ops, 3, line_no, mnem, f"{mnem} Ra, Rb, label")
            ra, rb = _reg(ops[0], line_no), _reg(ops[1], line_no)
            tgt = ops[2]
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", tgt):
                if tgt.lower() not in labels:
                    raise AsmError(f"line {line_no}: undefined label '{tgt}'")
                off = labels[tgt.lower()] - (pc + 1)
            else:
                off = _num(tgt, line_no, "offset")
            _check_range(off, -32, 31, line_no, "branch offset")
            word = (op << 12) | (ra << 9) | (rb << 6) | (off & 0x3F)
        elif mnem == "JMP":
            _expect(ops, 1, line_no, mnem, "JMP label")
            tgt = ops[0]
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", tgt):
                if tgt.lower() not in labels:
                    raise AsmError(f"line {line_no}: undefined label '{tgt}'")
                addr = labels[tgt.lower()]
            else:
                addr = _check_range(_num(tgt, line_no, "jump target"), 0, 255, line_no, "jump target")
            word = (op << 12) | addr
        else:  # HALT
            _expect(ops, 0, line_no, mnem, "HALT")
            word = 0xF000

        if mnem in WRITES_RD and pseudo != "NOP" and ((word >> 9) & 7) == 0:
            warnings.append(f"line {line_no}: writes R0; by convention R0 stays 0")
        words.append(word)
        listing.append((pc, word, src))
    return words, warnings, listing


def to_hex(words):
    return "".join(f"{w:04X}\n" for w in words)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Assembler for the CCEE 324 dual-core processor")
    ap.add_argument("source", help=".asm file")
    ap.add_argument("-o", "--output", help="output .hex file (default: same name with .hex)")
    ap.add_argument("-l", "--listing", action="store_true", help="print address, hex and source for each instruction")
    args = ap.parse_args(argv)
    out = args.output or re.sub(r"\.asm$", "", args.source) + ".hex"
    try:
        with open(args.source, encoding="utf-8") as f:
            words, warnings, listing = assemble_text(f.read())
    except AsmError as e:
        print(f"error: {args.source}: {e}", file=sys.stderr)
        return 1
    for w in warnings:
        print(f"warning: {args.source}: {w}", file=sys.stderr)
    with open(out, "w", encoding="utf-8") as f:
        f.write(to_hex(words))
    if args.listing:
        for pc, word, src in listing:
            print(f"{pc:3d}  {word:04X}  {src}")
    print(f"{args.source}: {len(words)} instructions -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

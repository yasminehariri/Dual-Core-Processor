"""Pictures of the processor running - the Python counterpart of Questa's wave window
and Quartus's RTL Viewer, drawn with matplotlib.

Two views:
    viewer  (default) a live block diagram of both cores and the shared memory.
            Step through the program with the buttons, the slider or the arrow keys
            and watch the PC, the instruction, the ALU, the registers and the memory change.
    waves   (--waves) a waveform plot like Questa: PCs, instructions, registers and
            memory bytes drawn over the clock cycles.

Examples (from the repo folder):
    python -m python_sim.visual --demo 2
    python -m python_sim.visual --demo 3 --waves
    python -m python_sim.visual --prog0 programs/demo1_core0.asm --prog1 programs/demo1_core1.asm --data programs/data1.hex
    python -m python_sim.visual --demo 1 --waves --save docs/waves_demo1.png      # save instead of opening a window
    python -m python_sim.visual --demo 2 --frame 6 --save docs/demo2_cycle6.png    # save one viewer frame

Needs matplotlib:  python -m pip install matplotlib
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from typing import Optional

from .core import CoreWires
from .disasm import disassemble
from .dual_core import DualCoreSystem
from .run import REPO, load_program
from .shared_mem import SharedMemory

DEMOS = {
    "1": ("demo1_core0.asm", "demo1_core1.asm", "data1.hex", "Demo 1: independent cores + shared memory"),
    "2": ("demo2_core0.asm", "demo2_core1.asm", "data2.hex", "Demo 2: flag synchronization"),
    "3": ("demo3_core0.asm", "demo3_core1.asm", "data3.hex", "Demo 3: parallel sum on two cores"),
    "single": ("demo3_single.asm", "halt.asm", "data3.hex", "Demo 3: the same sum on one core"),
    "conflict": ("conflict_core0.asm", "conflict_core1.asm", None, "Write conflict: Core 0 wins"),
}
ALU_OPS = ["+", "-", "AND", "OR", "XOR", "NOR", "<<", ">>"]

# colours (light, friendly)
INK, MUTED, EDGE = "#1F2A44", "#6B7489", "#9AA3B5"
C0, C0_BG = "#3F74C4", "#E3EEFB"
C1, C1_BG = "#8A55C2", "#F1E8FB"
ACTIVE, ACTIVE_BG = "#2F8A5E", "#DDF3E7"
WRITE, WRITE_BG = "#C77A0A", "#FFE9B8"
READ_EDGE = "#3F74C4"
IDLE_BG = "#F4F6FA"


# ============================================================ recording
@dataclass
class Frame:
    """The machine AFTER `cycle` clock edges. `wires[i]` = what core i executed in the
    cycle that just ended (None for the start frame or if the core was already halted)."""
    cycle: int
    pcs: tuple[int, int]
    halted: tuple[int, int]
    regs: tuple[list[int], list[int]]
    counts: tuple[int, int]
    mem: list[int]
    wires: tuple[Optional[CoreWires], Optional[CoreWires]] = (None, None)
    mem_written: dict[int, int] = field(default_factory=dict)     # addr -> core that wrote it


def snapshot(s: DualCoreSystem, wires=(None, None), written=None) -> Frame:
    return Frame(s.cycle, (s.core0.pc, s.core1.pc), (s.core0.halted, s.core1.halted),
                 (s.core0.dbg_regs(), s.core1.dbg_regs()), (s.core0.cycle_count, s.core1.cycle_count),
                 list(s.mem.mem), wires, written or {})


def record(prog0: str, prog1: str, data: Optional[str], max_cycles: int = 1000) -> list[Frame]:
    s = DualCoreSystem(load_program(prog0), load_program(prog1), SharedMemory(data))
    frames = [snapshot(s)]
    while not s.both_halted and s.cycle < max_cycles:
        rec = s.clock()
        written = {}
        for i, w in enumerate(rec.wires):          # Core 1 writes first, Core 0 last (Core 0 wins)
            if w is not None and w.mem_we:
                written[w.mem_addr] = i if w.mem_addr not in written or i == 0 else written[w.mem_addr]
        frames.append(snapshot(s, rec.wires, written))
    return frames


# ============================================================ viewer
def draw_frame(ax, frames: list[Frame], k: int, title: str) -> None:
    """Draw frame k into the axes `ax` (cleared first)."""
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

    ax.clear()
    f = frames[k]
    prev = frames[k - 1] if k > 0 else f
    last = len(frames) - 1
    ax.set_xlim(0, 100); ax.set_ylim(0, 64); ax.axis("off")

    def box(x, y, w, h, fc, ec, lw=1.3, r=0.8):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw))

    def txt(x, y, s, size=9, color=INK, weight="normal", ha="center", va="center", family=None):
        ax.text(x, y, s, fontsize=size, color=color, weight=weight, ha=ha, va=va, family=family)

    # ---- header
    txt(1.5, 62.3, title, 13, INK, "bold", ha="left")
    if k == 0:
        what = "start (after reset, nothing executed yet)"
    else:
        what = f"after clock cycle {f.cycle - 1}  (step {k} of {last})"
    txt(1.5, 59.9, what, 10, MUTED, ha="left")
    done = all(f.halted)
    txt(98.5, 62.3, "BOTH CORES HALTED" if done else "running", 10, ACTIVE if done else MUTED, "bold", ha="right")

    # ---- the two cores
    for i, x0 in enumerate((1.5, 51.0)):
        col, bg = (C0, C0_BG) if i == 0 else (C1, C1_BG)
        w = f.wires[i]
        box(x0, 23.5, 47.5, 34, "white", col, lw=2, r=1.2)
        txt(x0 + 2, 55.1, f"Core {i}", 12, col, "bold", ha="left")
        state = "HALTED" if f.halted[i] else "running"
        txt(x0 + 45.5, 55.1, f"{state}   |   cycles: {f.counts[i]}", 9, MUTED, ha="right")

        # instruction that just executed
        if w is None:
            line = "(halted, executes nothing)" if (k > 0 and prev.halted[i]) else "waiting for the first clock edge"
            box(x0 + 2, 49.5, 43.5, 3.6, IDLE_BG, EDGE)
            txt(x0 + 23.75, 51.3, line, 9.5, MUTED)
        else:
            box(x0 + 2, 49.5, 43.5, 3.6, bg, col)
            txt(x0 + 3.2, 51.3, f"pc {w.pc:3d}", 9.5, col, "bold", ha="left", family="monospace")
            txt(x0 + 11.5, 51.3, f"{w.instr:04X}", 9.5, MUTED, ha="left", family="monospace")
            txt(x0 + 18.5, 51.3, disassemble(w.instr), 10.5, INK, "bold", ha="left", family="monospace")

        # mini datapath: which parts were used this cycle
        stages = [("PC", True), ("IMEM", True), ("DECODE\nCONTROL", True),
                  ("REGS\nREAD", w is not None and not w.ctl.halt and not w.ctl.jump),
                  ("ALU", w is not None and (w.ctl.reg_write and w.ctl.wb_sel == 0 or w.ctl.branch)),
                  ("MEM", w is not None and (w.ctl.mem_read or w.mem_we)),
                  ("WRITE\nBACK", w is not None and bool(w.reg_we))]
        sw, sg = 5.6, 0.73
        for j, (name, on) in enumerate(stages):
            on = on and w is not None
            sx = x0 + 2 + j * (sw + sg)
            box(sx, 41.7, sw, 5.6, ACTIVE_BG if on else IDLE_BG, ACTIVE if on else EDGE, lw=1.6 if on else 1, r=0.6)
            txt(sx + sw / 2, 44.5, name, 7.2, ACTIVE if on else MUTED, "bold" if on else "normal")
            if j < len(stages) - 1:
                ax.add_patch(FancyArrowPatch((sx + sw, 44.5), (sx + sw + sg, 44.5), arrowstyle="-|>", mutation_scale=7, color=EDGE, lw=0.8))

        # what the ALU / memory / PC did
        if w is not None:
            notes = []
            if w.ctl.reg_write and w.ctl.wb_sel == 0:
                b_name = f"{w.f.imm6_sext:02X}" if w.ctl.alu_src else f"{w.rd2:02X}"
                notes.append(f"ALU: {w.rd1:02X} {ALU_OPS[w.ctl.alu_op]} {b_name} = {w.alu_result:02X}   Z={w.zero} C={w.carry} V={w.overflow}")
            if w.ctl.branch:
                notes.append(f"compare R{w.f.rd} with R{w.f.rs}: {'equal' if w.zero else 'not equal'} -> branch {'TAKEN' if w.branch_taken else 'not taken'}")
            if w.ctl.jump:
                notes.append(f"jump to instruction {w.f.addr8}")
            if w.ctl.mem_read:
                notes.append(f"read Mem[{w.mem_addr:02X}] = {w.mem_rdata:02X}")
            if w.mem_we:
                notes.append(f"write Mem[{w.mem_addr:02X}] <- {w.mem_wdata:02X}")
            if w.reg_we:
                notes.append(f"R{w.f.rd} <- {w.wb_data:02X}")
            if w.ctl.halt:
                notes.append("HALT: the PC stops here")
            for n_i, n in enumerate(notes[:3]):
                txt(x0 + 2.4, 38.8 - n_i * 2.4, "• " + n, 8.6, INK, ha="left", family="monospace")

        # registers R0..R7 (changed ones highlighted)
        txt(x0 + 2.2, 31.5, "Registers", 8.5, MUTED, ha="left")
        for r in range(8):
            rx = x0 + 2 + r * 5.45
            changed = k > 0 and f.regs[i][r] != prev.regs[i][r]
            box(rx, 25.1, 5.0, 5.0, WRITE_BG if changed else "white", WRITE if changed else EDGE, lw=1.6 if changed else 0.9, r=0.5)
            txt(rx + 2.5, 28.9, f"R{r}", 7.5, MUTED)
            txt(rx + 2.5, 26.7, f"{f.regs[i][r]:02X}", 10, WRITE if changed else INK, "bold" if changed else "normal", family="monospace")

        # next PC
        txt(x0 + 45.5, 31.5, f"next pc = {f.pcs[i]}", 8.5, col, "bold", ha="right")

    # ---- shared memory: 16 x 16 grid
    gx, gy, cw, ch = 9.0, 0.6, 5.1, 1.1
    txt(1.5, 21.3, "Shared data memory (256 bytes)", 10.5, INK, "bold", ha="left")
    txt(98.5, 21.3, "orange = written this cycle  |  blue outline = read this cycle", 8.2, MUTED, ha="right")
    reads = {w.mem_addr: i for i, w in enumerate(f.wires) if w is not None and w.ctl.mem_read}
    for c in range(16):
        txt(gx + c * cw + cw / 2, gy + 16 * ch + 0.5, f"{c:X}", 7, MUTED)
    for r in range(16):
        txt(gx - 1.8, gy + (15 - r) * ch + ch / 2, f"{r:X}0", 7, MUTED, family="monospace")
        for c in range(16):
            a = r * 16 + c
            v = f.mem[a]
            x, y = gx + c * cw, gy + (15 - r) * ch
            if a in f.mem_written:
                fc, ec, lw = WRITE_BG, WRITE, 1.5
            elif v:
                fc, ec, lw = "#EEF2F8", EDGE, 0.5
            else:
                fc, ec, lw = "white", "#E3E7EE", 0.4
            ax.add_patch(Rectangle((x, y), cw, ch, fc=fc, ec=ec, lw=lw))
            if a in reads:
                ax.add_patch(Rectangle((x + 0.15, y + 0.06), cw - 0.3, ch - 0.12, fc="none", ec=READ_EDGE, lw=1.6))
            if v or a in f.mem_written:
                txt(x + cw / 2, y + ch / 2, f"{v:02X}", 7, WRITE if a in f.mem_written else INK, "bold" if a in f.mem_written else "normal", family="monospace")


def viewer(frames: list[Frame], title: str, start: int = 0) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.widgets import Button, Slider

    fig = plt.figure(figsize=(14, 8.6))
    try:
        fig.canvas.manager.set_window_title("Dual-core processor viewer")
    except Exception:
        pass
    pic = fig.add_axes([0, 0.08, 1, 0.92])
    state = {"k": max(0, min(start, len(frames) - 1)), "playing": False}
    widgets = {}

    def build_controls():
        bx = [0.18, 0.26, 0.34, 0.42, 0.50]
        names = ["|< first", "< prev", "next >", "last >|", "play"]
        btns = []
        for x, n in zip(bx, names):
            a = fig.add_axes([x, 0.015, 0.075, 0.045])
            btns.append(Button(a, n, color="#EEF2F8", hovercolor="#DCE6F5"))
        sa = fig.add_axes([0.62, 0.025, 0.3, 0.03])
        sl = Slider(sa, "step", 0, len(frames) - 1, valinit=state["k"], valstep=1, color="#9CC0F0")
        btns[0].on_clicked(lambda e: go(0))
        btns[1].on_clicked(lambda e: go(state["k"] - 1))
        btns[2].on_clicked(lambda e: go(state["k"] + 1))
        btns[3].on_clicked(lambda e: go(len(frames) - 1))
        btns[4].on_clicked(lambda e: toggle())
        sl.on_changed(lambda v: go(int(v), from_slider=True))
        widgets.update(btns=btns, slider=sl)

    def go(k, from_slider=False):
        k = max(0, min(k, len(frames) - 1))
        state["k"] = k
        redraw()
        if not from_slider and int(widgets["slider"].val) != k:
            widgets["slider"].set_val(k)

    def redraw():
        draw_frame(pic, frames, state["k"], title)
        fig.canvas.draw_idle()

    timer = fig.canvas.new_timer(interval=700)

    def tick():
        if state["k"] >= len(frames) - 1:
            toggle(False)
        else:
            go(state["k"] + 1)

    timer.add_callback(tick)

    def toggle(on=None):
        state["playing"] = (not state["playing"]) if on is None else on
        widgets["btns"][4].label.set_text("pause" if state["playing"] else "play")
        (timer.start if state["playing"] else timer.stop)()
        fig.canvas.draw_idle()

    def on_key(e):
        if e.key in ("right", "n"):
            go(state["k"] + 1)
        elif e.key in ("left", "p"):
            go(state["k"] - 1)
        elif e.key == "home":
            go(0)
        elif e.key == "end":
            go(len(frames) - 1)
        elif e.key == " ":
            toggle()

    fig.canvas.mpl_connect("key_press_event", on_key)
    build_controls()
    redraw()
    plt.show()


# ============================================================ waves
def waves(frames: list[Frame], title: str):
    """Questa-style waveform plot. Returns the matplotlib figure."""
    import matplotlib.pyplot as plt

    n = len(frames) - 1                      # number of cycles executed
    rows = []                                # (label, values per cycle, kind, colour)

    def per_cycle(fn):
        return [fn(frames[c]) for c in range(n + 1)]

    for i, col in ((0, C0), (1, C1)):
        rows.append((f"core{i} pc", per_cycle(lambda fr, i=i: fr.pcs[i]), "dec", col))
        # instruction executed in cycle c = wires of frame c+1
        rows.append((f"core{i} instr", [(disassemble(frames[c + 1].wires[i].instr) if c < n and frames[c + 1].wires[i] else "")
                                         for c in range(n + 1)], "text", col))
        for r in range(1, 8):
            vals = per_cycle(lambda fr, i=i, r=r: fr.regs[i][r])
            if any(v != vals[0] for v in vals):
                rows.append((f"core{i} R{r}", vals, "hex", col))
    written = sorted({a for fr in frames for a in fr.mem_written})
    for a in written:
        rows.append((f"Mem[{a:02X}]", per_cycle(lambda fr, a=a: fr.mem[a]), "hex", WRITE))
    rows.append(("core0 halted", per_cycle(lambda fr: fr.halted[0]), "bit", C0))
    rows.append(("core1 halted", per_cycle(lambda fr: fr.halted[1]), "bit", C1))

    h = 0.5 + 0.42 * (len(rows) + 1)
    width = max(10.0, min(26.0, 2.2 + 0.62 * (n + 1)))
    fig, ax = plt.subplots(figsize=(width, h))
    ax.set_xlim(-2.6, n + 1); ax.set_ylim(-1.0, len(rows) + 1.2); ax.axis("off")
    ax.text(-2.6, len(rows) + 0.95, title + "  -  waveforms", fontsize=12, weight="bold", color=INK, va="center")

    # clock
    y = len(rows)
    xs, ys = [], []
    for c in range(n + 1):
        xs += [c, c, c + 0.5, c + 0.5]; ys += [y - 0.3, y + 0.3, y + 0.3, y - 0.3]
    xs.append(n + 1); ys.append(y - 0.3)
    ax.plot(xs, ys, color=MUTED, lw=1)
    ax.text(-0.2, y, "clk", ha="right", va="center", fontsize=8.5, color=MUTED, family="monospace")
    for c in range(n + 1):
        ax.text(c + 0.5, -0.85, str(c), ha="center", fontsize=7, color=MUTED)
        ax.axvline(c, color="#EEF1F6", lw=0.6, zorder=0)

    for ri, (label, vals, kind, col) in enumerate(rows):
        y = len(rows) - 1 - ri
        ax.text(-0.2, y, label, ha="right", va="center", fontsize=8.5, color=col, family="monospace")
        if kind == "bit":
            xs, ys = [], []
            for c, v in enumerate(vals):
                xs += [c, c + 1]; ys += [y - 0.28 + 0.56 * v] * 2
            ax.plot(xs, ys, color=col, lw=1.6, drawstyle="steps-post")
            continue
        # bus: segments of equal value
        c = 0
        while c <= n:
            e = c
            while e + 1 <= n and vals[e + 1] == vals[c]:
                e += 1
            x1, x2 = c + 0.06, e + 1 - 0.06
            v = vals[c]
            empty = v == "" or v is None
            ax.fill([x1, x1 + 0.12, x2 - 0.12, x2, x2 - 0.12, x1 + 0.12], [y, y + 0.28, y + 0.28, y, y - 0.28, y - 0.28],
                    color="#F4F6FA" if empty else "white", ec=EDGE if empty else col, lw=1)
            if not empty:
                s = f"{v:02X}" if kind == "hex" else (str(v) if kind == "dec" else v)
                room = (x2 - x1) * (12 if kind == "text" else 9)
                if kind == "text" and len(s) > room:
                    s = s.split()[0]
                ax.text((x1 + x2) / 2, y, s, ha="center", va="center", fontsize=7 if kind == "text" else 8,
                        color=INK, family="monospace", clip_on=True)
            c = e + 1
    fig.tight_layout()
    return fig


# ============================================================ CLI
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Pictures of the dual-core processor running (viewer or waveforms)")
    ap.add_argument("--demo", choices=sorted(DEMOS), help="run a built-in demo: 1, 2, 3, single, conflict")
    ap.add_argument("--prog0", help="Core 0 program (.asm or .hex)")
    ap.add_argument("--prog1", help="Core 1 program (.asm or .hex)")
    ap.add_argument("--data", help="shared memory init file (.hex)")
    ap.add_argument("--title", help="title shown on the picture")
    ap.add_argument("--waves", action="store_true", help="show waveforms instead of the block-diagram viewer")
    ap.add_argument("--frame", type=int, default=0, help="viewer: step to open on (or to save)")
    ap.add_argument("--save", help="save a PNG instead of opening a window")
    ap.add_argument("--max-cycles", type=int, default=1000)
    args = ap.parse_args(argv)

    if args.demo:
        p0, p1, d, t = DEMOS[args.demo]
        prog0, prog1 = os.path.join(REPO, "programs", p0), os.path.join(REPO, "programs", p1)
        data = os.path.join(REPO, "programs", d) if d else None
        title = args.title or t
    elif args.prog0 and args.prog1:
        prog0, prog1, data = args.prog0, args.prog1, args.data
        title = args.title or f"{os.path.basename(prog0)} + {os.path.basename(prog1)}"
    else:
        ap.error("give --demo, or both --prog0 and --prog1")

    try:
        import matplotlib
    except ImportError:
        print("matplotlib is needed for the pictures:  python -m pip install matplotlib", file=sys.stderr)
        return 1
    if args.save:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    frames = record(prog0, prog1, data, args.max_cycles)
    if not all(frames[-1].halted):
        print(f"warning: not both halted after {args.max_cycles} cycles", file=sys.stderr)

    if args.waves:
        fig = waves(frames, title)
        if args.save:
            fig.savefig(args.save, dpi=160, facecolor="white")
            print(f"saved {args.save}")
        else:
            plt.show()
        return 0

    if args.save:
        fig = plt.figure(figsize=(14, 8.6))
        k = max(0, min(args.frame, len(frames) - 1))
        draw_frame(fig.add_axes([0, 0, 1, 1]), frames, k, title)
        fig.savefig(args.save, dpi=130, facecolor="white")
        print(f"saved {args.save} (step {k} of {len(frames) - 1})")
        return 0
    viewer(frames, title, args.frame)
    return 0


if __name__ == "__main__":
    sys.exit(main())

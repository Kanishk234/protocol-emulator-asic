#!/usr/bin/env python3
"""Generate test/fabric_settle_gl.vh and test/fabric_settle_rtl.vh (D-023).

In 4-state zero-delay simulation the fabric's unused routing is a problem silicon does not have.
Unused wires sit on default mux inputs and form combinational loops, across tiles and inside them:
  - a loop that starts at X stays X, and gate-level LUTs pass X on from inputs the configured
    function ignores (silicon: the loop holds some definite 0/1, the LUT ignores it);
  - while a new configuration is written over an old one, a half-written configuration can close
    a loop that oscillates; silicon rings until the load completes (design in reset, every pin
    parked), but a zero-delay simulator never advances past it, unless the loop is X.
So the testbench holds the fabric's nets at X for the whole of a load (tb.hold_x high), so no
half-written configuration can ring, and after the load pulses the inter-tile wires to 0
(tb.settle_routing, mux selects known, design in reset) so the loops settle to definite values.
A net driven by a latch or flip-flop returns to its stored value on release, so configuration
and state survive (the latches keep updating underneath the force); combinational nets
recompute from them.
Excluded: the configuration path (FrameData/FrameStrobe and every buffer between a tile port and
a configuration latch's D or GATE, found by tracing the tile netlists), where an X pulse would
overwrite configuration bits.

Gate level: the inter-tile wires of the macro netlist and every internal net of each tile
netlist (macro/<fabric>/tiles/*.nl.v). RTL: the inter-tile wires only (the RTL LUT model resolves
don't-care X by itself; test_bitstream.py orders the RTL reloads, D-023).

Usage: scripts/gen_fabric_settle.py [fabric]      (default warp_tiny)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FABRIC = sys.argv[1] if len(sys.argv) > 1 else "warp_tiny"
MACRO = ROOT / "macro" / FABRIC
HIER = "user_project.u_fabric"
CONFIG_PORTS = ("FrameData", "FrameStrobe")
LATCH = re.compile(r"sg13cmos5l_dl\w+")
PASS_THROUGH = re.compile(r"sg13cmos5l_(buf|inv|dlygate|clkbuf)\w*")
OUT_PINS = {"X", "Y", "Q", "Q_N", "Z", "L_HI", "L_LO"}


def norm(n):
    return n.strip().lstrip("\\").strip()


def esc(n):
    """A net name as a hierarchical path component."""
    return n if re.fullmatch(r"[A-Za-z_]\w*", n) else f"\\{n} "


def tile_internal_nets(nl: Path):
    """(forceable internal nets, excluded config-path nets) of one tile gate-level netlist."""
    text = nl.read_text()
    body = text[text.index(");") + 2:]                # after the port list
    ports = {norm(m.group(2)) for m in re.finditer(
        r"^\s*(input|output|inout)\s+(?:\[[^\]]*\]\s*)?(\\?\S+)\s*;", body, re.M)}
    wires = {}                                          # name -> declared with a range?
    for m in re.finditer(r"^\s*wire\s+(\[[^\]]*\]\s*)?(\\?\S+)\s*;", body, re.M):
        wires[norm(m.group(2))] = bool(m.group(1))
    drivers, latch_inputs, port_drivers = {}, set(), set()
    for m in re.finditer(r"^\s*(sg13cmos5l_\w+)\s+\S+\s*\((.*?)\);", body, re.S | re.M):
        typ, pins_txt = m.groups()
        pins = {p: norm(n) for p, n in re.findall(r"\.(\w+)\((.*?)\)\s*(?:,|$)", pins_txt, re.S)}
        for p, n in pins.items():
            if p in OUT_PINS:
                drivers[n] = (typ, pins)
        if LATCH.fullmatch(typ):
            latch_inputs |= {pins.get("D"), pins.get("GATE"), pins.get("GATE_N")} - {None}
    # nets that drive the FrameData_O/FrameStrobe_O outputs (the chain to the next tile)
    for m in re.finditer(r"assign\s+(.*?)\s*=\s*(.*?);", body):
        lhs, rhs = norm(m.group(1)), norm(m.group(2))
        if lhs.startswith(CONFIG_PORTS):
            port_drivers.add(rhs)
    for n, (typ, pins) in drivers.items():
        if n.startswith(CONFIG_PORTS):
            port_drivers |= {v for p, v in pins.items() if p not in OUT_PINS}
    excluded, todo = set(), list(latch_inputs | port_drivers)
    while todo:
        n = todo.pop()
        if n in excluded:
            continue
        excluded.add(n)
        d = drivers.get(n)
        if d and PASS_THROUGH.fullmatch(d[0]):
            todo += [v for p, v in d[1].items() if p not in OUT_PINS]
    base = lambda n: re.sub(r"\s*\[\d+\]$", "", n)
    nets = [n for n in wires if n not in ports and n not in excluded and base(n) not in excluded
            and not n.startswith(CONFIG_PORTS)]
    return nets, excluded


def gl_nets():
    """(inter-tile wires, tile-internal nets, number of excluded configuration-path nets)."""
    top = (MACRO / f"{FABRIC}.nl.v").read_text()
    inter = [esc(m.group(1)) for m in re.finditer(
        r"^\s*wire\s+\\?(Tile_X\d+Y\d+_\w+(?:\[\d+\])?)\s*;", top, re.M)
        if not m.group(1).split("_", 2)[2].startswith(CONFIG_PORTS)]
    internal, n_ex, cache = [], 0, {}
    for m in re.finditer(r"^\s*(\w+)\s+(Tile_X\d+Y\d+_\w+)\s*\(", top, re.M):
        mod, inst = m.groups()
        if mod not in cache:
            cache[mod] = tile_internal_nets(MACRO / "tiles" / f"{mod}.nl.v")
        nets, excluded = cache[mod]
        n_ex += len(excluded)
        internal += [f"{inst}.{esc(n)}" for n in nets]
    return inter, internal, n_ex


def rtl_nets():
    text = (MACRO / f"{FABRIC}.v").read_text()
    return [m.group(1) for m in re.finditer(
        r"^\s*wire\s*(?:\[[^\]]*\])?\s*(Tile_X\d+Y\d+_\w+)\s*;", text, re.M)
        if not m.group(1).split("_", 2)[2].startswith(CONFIG_PORTS)]


def emit(path, source, settle, unsettle, note=""):
    """settle (a pulse to 0) acts on `settle`; hold_x (X while held) on `unsettle`. Forcing
    internal nets to 0 would leave gates inconsistent with their inputs, and zero-delay loops
    through the gate-level LUTs can then glitch forever; X is always consistent."""
    if not settle or not unsettle:
        raise SystemExit(f"no nets found in {source}")
    out = [f"// Generated by scripts/gen_fabric_settle.py from {source}; do not edit.",
           f"// settle: {len(settle)} nets to 0; unsettle: {len(unsettle)} nets to X (D-023){note}."]
    # settle: a 1 ns pulse to 0 on the rising edge of settle_routing
    out += ["always @(posedge settle_routing) begin"]
    out += [f"  force {HIER}.{n} = 1'b0;" for n in settle]
    out += ["  #1;"]
    out += [f"  release {HIER}.{n};" for n in settle]
    out += ["end"]
    # hold_x: X for as long as hold_x is high (the whole load), so no ring can form
    out += ["always @(posedge hold_x) begin"]
    out += [f"  force {HIER}.{n} = 'bx;" for n in unsettle]
    out += ["end", "always @(negedge hold_x) begin"]
    out += [f"  release {HIER}.{n};" for n in unsettle]
    out += ["end"]
    path.write_text("\n".join(out) + "\n")
    print(f"{path.relative_to(ROOT)}: settle {len(settle)}, unsettle {len(unsettle)}{note}")


inter, internal, n_ex = gl_nets()
emit(ROOT / "test/fabric_settle_gl.vh", f"macro/{FABRIC}/{FABRIC}.nl.v + tiles/*.nl.v",
     inter, inter + internal, f"; {n_ex} configuration-path nets excluded")
rtl = rtl_nets()
emit(ROOT / "test/fabric_settle_rtl.vh", f"macro/{FABRIC}/{FABRIC}.v", rtl, rtl)

"""WARP compile flow (PHASE2 "Protocol compile flow"): user Verilog + pin map -> .wbit + report.

    python -m compile.compile --arch arch/warp_tiny --pins pins.yaml -o build/compile/uart \
        protocols/uart/src/*.v

Pin map (YAML):
    top: uart_top                 # user top module
    pins:                         # user port (or port[bit]) -> WARP pin (arch/<arch>/pins.csv)
      clk: clk
      rst_n: rst_n
      rx: FAB_IN0
      tx: FAB_OUT0
      sda_o: FAB_IO0.o            # bidirectional pins: .o value, .oe output enable, .i input
      sda_oe: FAB_IO0.oe
      sda_i: FAB_IO0.i
      h_rdata[0]: h_rdata0        # host channel (architectures that have it, D-024)

Steps: a generated wrapper `warp_top` (one explicit IOBUF per used IO cell, wired as in the
fabric) around the user top; Yosys `synth_fabulous` with the tile library's primitives; nextpnr-generic
`--uarch fabulous` with the fabric's pips/bels (timing from the hardened tiles' corners); WARP's
bitgen (compile/bitgen.py, the FABulous frame format); the words go into a .wbit stamped with the
ARCH_VERSION.
Unmapped user inputs are tied to 0; unmapped outputs are left open (both reported).
"""

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from compile.bitfile import BitFile
from compile.bitgen import gen_words

ROOT = Path(__file__).resolve().parents[2]
WRAPPER_TOP = "warp_top"
SLOW_CORNER = "nom_slow_1p08V_125C"   # timing sign-off corner of the hardened tiles
FFS = ["$_DFF_P_", "$_DFFE_PP_", "$_SDFF_PP?_", "$_SDFFE_PP?P_", "$_DLATCH_?_"]


class CompileError(Exception):
    pass


def tool(name):
    path = shutil.which(name)
    if not path:
        oss = Path.home() / "oss-cad-suite" / "bin" / name
        if oss.exists():
            return str(oss)
        raise CompileError(f"{name} not found (OSS CAD Suite, docs/VERSIONS.md)")
    return path


def run(cmd, log, cwd, env=None):
    with open(log, "w") as f:
        r = subprocess.run(cmd, cwd=cwd, stdout=f, stderr=subprocess.STDOUT, env=env)
    if r.returncode:
        tail = Path(log).read_text(errors="replace").splitlines()[-25:]
        raise CompileError(f"{Path(cmd[0]).name} failed (log {log}):\n" + "\n".join(tail))


def load_arch(arch_dir: Path):
    meta = yaml.safe_load((arch_dir / "arch.yaml").read_text())
    pins = {}
    with open(arch_dir / "pins.csv", newline="") as f:
        for row in csv.DictReader(f):
            pins[row["pin"]] = row
    return meta, pins


def user_ports(sources, top, work):
    """Port names, directions and widths of the user top, via Yosys."""
    js = work / "ports.json"
    script = " ".join(f"read_verilog -sv {Path(s).resolve()};" for s in sources)
    run([tool("yosys"), "-q", "-p", f"{script} hierarchy -top {top}; proc; write_json {js}"],
        work / "ports.log", work)
    mod = json.loads(js.read_text())["modules"].get(top)
    if mod is None:
        raise CompileError(f"top module {top} not found")
    return {n: (p["direction"], len(p["bits"])) for n, p in mod["ports"].items()}


ROLE_OF = {"clock": "i", "in": "i", "out": "o", "out_en": "oe"}


def resolve(pinmap, ports, arch_pins):
    """Map every user port bit to a WARP pin role. Returns {pin: {role: 'port[bit]'}}.
    Roles are the IO cell's fabric-side ports: i (pad -> fabric, the cell's OUT), o (the cell's
    IN) and oe (the cell's EN). Pin directions in pins.csv: clock/in (i), out (o), out_en (oe:
    an output carried on a cell's enable wire, e.g. host-channel bits) and inout (.o/.oe/.i)."""
    use = {}
    for key, target in pinmap.items():
        m = re.fullmatch(r"(\w+)(?:\[(\d+)\])?", key)
        if not m or m.group(1) not in ports:
            raise CompileError(f"pin map: no port {key!r} in the user top")
        name, bit = m.group(1), m.group(2)
        direction, width = ports[name]
        if bit is None and width != 1:
            raise CompileError(f"pin map: {name} is {width} bits wide; map {name}[i]")
        if bit is not None and int(bit) >= width:
            raise CompileError(f"pin map: {key} out of range")
        ref = f"{name}[{bit}]" if bit is not None else name
        pin, _, role = str(target).partition(".")
        if pin not in arch_pins:
            raise CompileError(f"pin map: {pin!r} is not a pin of this architecture")
        kind = arch_pins[pin]["direction"]
        if kind == "inout":
            if role not in ("o", "oe", "i"):
                raise CompileError(f"pin map: bidirectional {pin} needs .o, .oe or .i")
        elif role:
            raise CompileError(f"pin map: {pin} takes no role suffix")
        else:
            role = ROLE_OF[kind]
        want = "input" if role == "i" else "output"
        if direction != want:
            raise CompileError(f"pin map: {key} is an {direction}, {target} needs an {want}")
        if role in use.setdefault(pin, {}):
            raise CompileError(f"pin map: {target} mapped twice")
        use[pin][role] = ref
    if "clk" not in use:
        raise CompileError("pin map: the user design must map its clock to `clk`")
    cells = {}
    for pin, roles in use.items():
        bel = arch_pins[pin]["bel"]
        for role in roles:
            if role in cells.setdefault(bel, {}):
                raise CompileError(f"pin map: {pin} and {cells[bel][role]} share IO cell {bel} ({role})")
            cells[bel][role] = pin
    return use


def cell_id(bel):
    return bel.replace("/", "_")


def wrapper(top, ports, use, arch_pins):
    """`warp_top`: one port per used IO cell (pad_<cell>), with the tile library's IOBUF
    instantiated explicitly, so its fabric-side ports are wired exactly as in the fabric: IN (o),
    EN (oe) and OUT (i) are independent signals (the pad logic is in the shell, not the fabric).
    An output without an enable gets EN = 1. The clock reaches the LCs through a GBUF."""
    cells = {}                                   # cell -> {role: pin}
    for pin, roles in use.items():
        for role in roles:
            cells.setdefault(arch_pins[pin]["bel"], {})[role] = pin
    decl, wires, body = [], [], []
    for bel, roles in cells.items():
        c = cell_id(bel)
        decl.append(f"inout wire pad_{c}")
        for r in roles:
            wires.append(f"wire w_{c}_{r};")
        o = f"w_{c}_o" if "o" in roles else "1'b0"
        oe = f"w_{c}_oe" if "oe" in roles else ("1'b1" if "o" in roles else "1'b0")
        i = f"w_{c}_i" if "i" in roles else ""
        body.append(f"(* keep *) IOBUF u_{c} (.PAD(pad_{c}), .IN({o}), .EN({oe}), .OUT({i}));")
        if "i" in roles and arch_pins[roles["i"]]["direction"] == "clock":
            wires.append(f"wire w_{c}_gclk;")
            body.append(f"GBUF u_{c}_gbuf (.IN(w_{c}_i), .OUT(w_{c}_gclk));")
    conn = {}   # port -> list of bit expressions (LSB first)
    for name, (direction, width) in ports.items():
        conn[name] = ["1'b0" if direction == "input" else None] * width
    for pin, roles in use.items():
        c = cell_id(arch_pins[pin]["bel"])
        for role, ref in roles.items():
            m = re.fullmatch(r"(\w+)(?:\[(\d+)\])?", ref)
            name, bit = m.group(1), int(m.group(2) or 0)
            clock = arch_pins[pin]["direction"] == "clock"
            conn[name][bit] = f"w_{c}_gclk" if clock else f"w_{c}_{role}"
    unmapped_in, unmapped_out, inst = [], [], []
    for name, bits in conn.items():
        direction = ports[name][0]
        for i, b in enumerate(bits):
            if b is None:
                unmapped_out.append(f"{name}[{i}]" if len(bits) > 1 else name)
            elif b == "1'b0" and direction == "input":
                unmapped_in.append(f"{name}[{i}]" if len(bits) > 1 else name)
        if direction == "output":
            if all(b is None for b in bits):
                inst.append(f".{name}()")
                continue
            wires += [f"wire nc_{name}_{i};" for i, b in enumerate(bits) if b is None]
            bits = [b if b is not None else f"nc_{name}_{i}" for i, b in enumerate(bits)]
        inst.append(f".{name}({{{', '.join(reversed(bits))}}})")
    text = ["// Generated by tools/compile/compile.py; do not edit.", "`default_nettype none",
            f"module {WRAPPER_TOP} (", "    " + ",\n    ".join(decl), ");"]
    text += ["    " + w for w in wires] + ["    " + b for b in body]
    text += [f"    {top} u_user (", "        " + ",\n        ".join(inst), "    );", "endmodule", ""]
    return "\n".join(text), unmapped_in, unmapped_out, cells


def synth_script(sources, out: Path, prim: Path, top: str = WRAPPER_TOP, params=None) -> str:
    """Yosys script. The pinned Yosys (0.66, docs/VERSIONS.md) has the older synth_fabulous,
    without the -ff/-clkbuf-map options the tile library's flow uses and with IO pad mapping
    hard-wired to the stock FABulous IO cell; so the IO pads (tile library IOBUF, output enable
    active high) are mapped here between synth_fabulous's stages; the clock buffer (GBUF) is
    instantiated in the wrapper."""
    plibs = ("FABULOUS_LC/yosys/primitives/prims.v", "IOBUF/yosys/primitives/IOBUF.v",
             "GBUF/yosys/primitives/GBUF.v", "SYS_RESET/yosys/primitives/SYS_RESET.v")
    maps = ("FABULOUS_LC/yosys/techmap/lut_map.v", "FABULOUS_LC/yosys/techmap/ff_map.v")
    opts = (f"-top {top} -lut 4 -carry ha -complex-dff -noregfile "
            + " ".join(f"-extra-plib {prim / p}" for p in plibs) + " "
            + " ".join(f"-extra-map {prim / m}" for m in maps))
    lines = [f"read_verilog -sv {Path(s).resolve()}" for s in sources]
    if top == WRAPPER_TOP:
        lines.append(f"read_verilog -sv {out / 'warp_top.v'}")
    if params:
        lines.append("chparam " + " ".join(f"-set {k} {v}" for k, v in params.items()) + f" {top}")
    lines += [
        f"synth_fabulous {opts} -run begin:map_iopad",
        "opt -full",
        "iopadmap -bits -outpad $__FABULOUS_OBUF IN:PAD -inpad $__FABULOUS_IBUF OUT:PAD "
        f"-toutpad $__FABULOUS_TBUF EN:IN:PAD -tinoutpad $__FABULOUS_IOBUF EN:OUT:IN:PAD {top}",
        f"techmap -map {prim / 'IOBUF/yosys/techmap/IOBUF_map.v'}",
        f"synth_fabulous {opts} -run map_iopad:check",
        # ABC maps the FF enable/reset logic once per FF; merge the identical LUTs it leaves
        "opt_merge -share_all",
        "clean",
        "hierarchy -check",
        "stat",
        f"write_json {out / 'design.json'}",
    ]
    return "\n".join(lines) + "\n"


def cell_estimate(design_json: Path, top: str) -> dict:
    """Resource estimate from the synthesized netlist, before place and route: LUTs (LUT1–4 and
    carry LUT4_HA, each one FABULOUS_LC), flip-flops, IO cells, and the logic cells they need.
    An LC has one output (the LUT or its flip-flop), so a flip-flop shares an LC only with the
    LUT that drives its D and nothing else; every other flip-flop takes an LC of its own."""
    mod = json.loads(design_json.read_text())["modules"][top]
    cells = [c for c in mod["cells"].values() if c["type"] != "$scopeinfo"]
    luts = [c for c in cells if re.fullmatch(r"LUT[1-4](_HA)?", c["type"])]
    ffs = [c for c in cells if c["type"].startswith("LUTFF")]
    ios = [c for c in cells if c["type"] == "IOBUF"]
    sinks = {}
    for c in cells:
        for p, bits in c["connections"].items():
            if c["port_directions"].get(p) == "input":
                for b in bits:
                    sinks[b] = sinks.get(b, 0) + 1
    for n in mod["ports"].values():
        if n["direction"] == "output":
            for b in n["bits"]:
                sinks[b] = sinks.get(b, 0) + 1
    lut_out = {c["connections"]["O"][0]: i for i, c in enumerate(luts) if c["connections"].get("O")}
    paired = set()
    for f in ffs:
        d = f["connections"]["D"][0]
        i = lut_out.get(d)
        if i is not None and i not in paired and sinks.get(d, 0) == 1:
            paired.add(i)
    other = sorted({c["type"] for c in cells} - {c["type"] for c in luts + ffs + ios})
    return {"luts": len(luts), "carry_luts": sum(c["type"] == "LUT4_HA" for c in luts),
            "ffs": len(ffs), "lcs": len(luts) + len(ffs) - len(paired), "io": len(ios),
            "other_cells": other}


def synth_only(sources, top, out, params=None) -> dict:
    """Synthesis for this fabric's cells only (no pins, no place and route), for designs whose
    ports cannot be placed on the current fabric (e.g. the host channel). Returns cell_estimate."""
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    tiles = Path(os.environ.get("WARP_TILES") or subprocess.check_output(
        [str(ROOT / "scripts" / "fetch_tiles.sh")], text=True).strip())
    (out / "synth.ys").write_text(synth_script(sources, out, tiles / "primitives", top, params))
    run([tool("yosys"), "-s", str(out / "synth.ys")], out / "synth.log", out)
    return cell_estimate(out / "design.json", top)


def check_frames(words, rows):
    """The stream must be what the shell's ConfigFSM expects: sync, then (header + `rows` data
    words) per frame, then a desync header (bit 20)."""
    from host.protocol import SYNC_WORD
    if not words or words[0] != SYNC_WORD:
        raise CompileError("bitstream does not start with the sync word")
    i = 1
    while i < len(words) and not (words[i] >> 20) & 1:
        strobe = words[i] & 0xFFFFF
        if strobe == 0 or strobe & (strobe - 1) or (words[i] >> 20) & 0x7F:
            raise CompileError(f"word {i}: not a frame header ({rows} rows per frame?)")
        i += 1 + rows
    if i != len(words) - 1 or words[i] != 1 << 20:
        raise CompileError(f"bitstream framing does not match {rows} rows per frame")


def parse_pnr_log(log: Path):
    text = log.read_text(errors="replace")
    util = {}
    for m in re.finditer(r"^Info:\s+(\w+):\s+(\d+)/\s*(\d+)\s+(\d+)%", text, re.M):
        util[m.group(1)] = {"used": int(m.group(2)), "available": int(m.group(3))}
    fmax = [float(x) for x in re.findall(r"Max frequency for clock[^:]*:\s*([\d.]+) MHz", text)]
    return util, (fmax[-1] if fmax else None)


def compile_design(sources, pins_file, arch_dir, out, seed=1):
    arch_dir, out = Path(arch_dir).resolve(), Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    meta, arch_pins = load_arch(arch_dir)
    spec = yaml.safe_load(Path(pins_file).read_text())
    top = spec["top"]
    fab = (ROOT / meta["macro"] / "fabulous").resolve()
    tiles = Path(os.environ.get("WARP_TILES") or subprocess.check_output(
        [str(ROOT / "scripts" / "fetch_tiles.sh")], text=True).strip())
    prim = tiles / "primitives"

    ports = user_ports(sources, top, out)
    use = resolve(spec["pins"], ports, arch_pins)
    wtext, unmapped_in, unmapped_out, cells = wrapper(top, ports, use, arch_pins)
    (out / "warp_top.v").write_text(wtext)

    pcf = "\n".join(f"set_io pad_{cell_id(bel)} {bel}" for bel in cells) + "\n"
    (out / "pins.pcf").write_text(pcf)

    (out / "synth.ys").write_text(synth_script(sources, out, prim))
    run([tool("yosys"), "-s", str(out / "synth.ys")], out / "synth.log", out)

    env = dict(os.environ, FAB_ROOT=str(fab))
    run([tool("nextpnr-generic"), "--uarch", "fabulous", "--json", str(out / "design.json"),
         "--write", str(out / "design_pnr.json"), "-o", f"fasm={out / 'design.fasm'}",
         "-o", f"pcf={out / 'pins.pcf'}", "-o", f"corner={SLOW_CORNER}",
         "--seed", str(seed), "--log", str(out / "pnr.log"), "--timing-allow-fail"],
        out / "pnr_stdout.log", out, env)

    # WARP bitgen (BUGS #13); every row, the edge rows included, is written
    words = gen_words(out / "design.fasm", fab / "bitStreamSpec.bin")
    check_frames(words, int(meta["config_rows"]))
    bf = BitFile(int(meta["arch_version"]), words)
    name = Path(pins_file).stem if Path(pins_file).stem != "pins" else top
    bf.save(out / f"{name}.wbit")

    util, fmax = parse_pnr_log(out / "pnr.log")
    report = {
        "design": top,
        "arch": meta["name"],
        "arch_version": f"0x{bf.arch_version:04X}",
        "words": len(words),
        "crc32": f"0x{bf.crc:08X}",
        "timing_corner": SLOW_CORNER,
        "fmax_mhz": fmax,
        "meets_50mhz": (fmax is not None and fmax >= 50.0),
        "utilisation": util,
        "pins": {pin: roles for pin, roles in use.items()},
        "unmapped_inputs_tied_0": unmapped_in,
        "unmapped_outputs_open": unmapped_out,
        "tools": tool_versions(),
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return out / f"{name}.wbit", report


def tool_versions():
    v = {}
    for t, args in (("yosys", ["-V"]), ("nextpnr-generic", ["--version"])):
        try:
            r = subprocess.run([tool(t)] + args, capture_output=True, text=True)
            v[t] = (r.stdout + r.stderr).strip().splitlines()[0]
        except Exception:  # noqa: BLE001 - informational only
            v[t] = "unknown"
    v["bitgen"] = "tools/compile/bitgen.py"
    return v


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", nargs="+")
    ap.add_argument("--pins", required=True, help="pin map YAML (top + pins)")
    ap.add_argument("--arch", default=str(ROOT / "arch" / "warp_tiny"))
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args(argv)
    try:
        path, rep = compile_design(a.sources, a.pins, a.arch, a.out, a.seed)
    except CompileError as e:
        print(f"compile: error: {e}", file=sys.stderr)
        return 1
    print(f"{path}: {rep['words']} words, CRC {rep['crc32']}, arch {rep['arch_version']}, "
          f"Fmax {rep['fmax_mhz']} MHz ({rep['timing_corner']})")
    for k, v in rep["utilisation"].items():
        print(f"  {k}: {v['used']}/{v['available']}")
    for w, lst in (("inputs tied to 0", rep["unmapped_inputs_tied_0"]),
                   ("outputs left open", rep["unmapped_outputs_open"])):
        if lst:
            print(f"  unmapped {w}: {', '.join(lst)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""What limits each design-set protocol on the chip's fabric (phase 3 input).

For every protocol compiled onto an architecture (`python -m compile.protocols`, its
`design.json` and `report.json` under the output directory), report:
  - logic cells used, and what the LUTs are for: each LUT is attributed to the function of the
    registers it feeds (the same method as profiling.workload, with register tables for the
    current sources); the hard primitives count as registers of their function (a timer is a
    `counter`, a shift register is `shift`), so the LUTs around them are their glue;
  - flip-flops, and the control sets (distinct clock-enable/reset pairs): each LUT tile has one,
    so a design needs at least as many LUT tiles as it has control sets (BUGS #15);
  - hard primitives used against those the fabric has;
  - the timing estimate and what its critical path ends in.

    python -m profiling.limits [--dir build/protocols] [--markdown FILE]
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRIM_FN = {"wp_timer": "counter", "wp_shift": "shift"}

# (regex on the flattened register name, function); first match wins. Names are the current
# sources with PRIMS = 1 (protocols/*), under the wrapper's u_user instance.
ROLES = {
    "uart": [(r"\.sync$", "sync"), (r"u_tx\.tx$", "pin"), (r"h_rdata$", "storage"),
             (r".*", "control")],
    "spi_ctrl": [(r"nedge$", "counter"), (r"samp$", "shift"), (r"miso_s$", "sync"),
                 (r"sck_o$|cs_n_o$|mosi_q$", "pin"), (r"h_rdata$", "storage"), (r".*", "control")],
    "i2c_ctrl": [(r"ackph$|ack_out$|ack_q$", "shift"), (r"sda_oe$|scl_oe$", "pin"),
                 (r"h_rdata$", "storage"), (r".*", "control")],
    "i2c_target": [(r"(^|\.)regs$|h_rdata$|dirty$", "storage"), (r"ptr$", "counter"),
                   (r"sda_q$|scl_q$", "sync"), (r"sda_oe$", "pin"), (r".*", "control")],
}


def is_ff(t):
    return t.startswith("LUTFF")


def is_lut(t):
    return re.fullmatch(r"LUT[1-4](_HA)?", t) is not None


def analyse(name, j, top="warp_top"):
    mod = j["modules"][top]
    cells = {k: c for k, c in mod["cells"].items() if c["type"] != "$scopeinfo"}
    names = {}
    for n, info in mod["netnames"].items():
        for b in info["bits"]:
            if isinstance(b, int) and (b not in names or ("$" in names[b] and "$" not in n)):
                names[b] = n.lstrip("\\")
    roles = ROLES.get(name, [(r".*", "control")])

    def role(reg):
        for rx, fn in roles:
            if re.search(rx, reg):
                return fn
        return "control"

    sinks = defaultdict(list)
    reg_fn = {}                                   # FF or primitive cell -> function
    ffs, ctrl, prims = Counter(), Counter(), Counter()
    for cn, c in cells.items():
        dirs = c.get("port_directions", {})
        for pn, bits in c["connections"].items():
            if dirs.get(pn) == "input":
                for b in bits:
                    if isinstance(b, int):
                        sinks[b].append(cn)
        t = c["type"]
        if is_ff(t):
            q = c["connections"].get("O", [])
            reg = re.sub(r"\[\d+\]$", "", names.get(q[0], cn)) if q else cn
            reg_fn[cn] = role(reg)
            ffs[reg_fn[cn]] += 1
            ctrl[(tuple(c["connections"].get("E", [])),
                  tuple(c["connections"].get("R", c["connections"].get("S", []))))] += 1
        elif t in PRIM_FN:
            reg_fn[cn] = PRIM_FN[t]
            prims[t] += 1

    memo = {}

    def reach(cn, stack=()):
        if cn in memo:
            return memo[cn]
        if cn in stack:
            return frozenset()
        c = cells[cn]
        dirs = c.get("port_directions", {})
        fns = set()
        for pn, bits in c["connections"].items():
            if dirs.get(pn) != "output":
                continue
            for b in bits:
                if not isinstance(b, int):
                    continue
                for s in sinks.get(b, []):
                    if s in reg_fn:
                        fns.add(reg_fn[s])
                    elif cells[s]["type"] == "IOBUF":
                        fns.add("pin")
                    else:
                        fns |= reach(s, stack + (cn,))
        memo[cn] = frozenset(fns)
        return memo[cn]

    luts = Counter()
    for cn, c in cells.items():
        if is_lut(c["type"]):
            fns = reach(cn)
            luts[next(iter(fns)) if len(fns) == 1 else ("shared" if fns else "unused")] += 1
    return {"luts": luts, "ffs": ffs, "control_sets": len(ctrl), "prims": prims}


def critical_path(pnr_log):
    """Last critical-path report of nextpnr: its end point and whether it touches a primitive."""
    text = pnr_log.read_text(errors="replace")
    blocks = text.split("Critical path report for clock")
    if len(blocks) < 2:
        return None
    last = blocks[-1].split("Max frequency")[0]
    ends = re.findall(r"Sink (\S+)", last)
    return {"through_primitive": bool(re.search(r"u_(timer|shift)\.u_bel", last)),
            "end": ends[-1] if ends else "?"}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default=str(ROOT / "build" / "protocols"))
    ap.add_argument("--markdown")
    a = ap.parse_args(argv)
    d = Path(a.dir)
    res = json.loads((d / "results.json").read_text())
    arch = res["arch"]
    fns = ["counter", "shift", "storage", "control", "sync", "pin", "shared"]
    rows = []
    for name, r in sorted(res["results"].items()):
        j = json.loads((d / name / "design.json").read_text())
        an = analyse(name, j)
        cp = critical_path(d / name / "pnr.log") if r.get("fits") else None
        rows.append((name, r, an, cp))
    lines = [f"| Protocol | fits {arch}? | LCs | LUTs: " + " / ".join(fns) + " | FFs | control sets | primitives | Fmax | critical path |",
             "|---|---|---|---|---|---|---|---|---|"]
    for name, r, an, cp in rows:
        lut_s = " / ".join(str(an["luts"].get(f, 0)) for f in fns)
        prim_s = ", ".join(f"{v} {k[3:]}" for k, v in sorted(an["prims"].items())) or "-"
        cps = "-" if not cp else ("through a primitive" if cp["through_primitive"] else "LUT/FF only")
        fmax = f"{r['fmax_mhz']:.1f}" if r.get("fmax_mhz") else "-"
        lines.append(f"| {name} | {'yes' if r['fits'] else 'no'} | {r['lcs']} | {lut_s} | "
                     f"{sum(an['ffs'].values())} | {an['control_sets']} | {prim_s} | {fmax} | {cps} |")
    out = "\n".join(lines)
    print(out)
    if a.markdown:
        Path(a.markdown).write_text(out + "\n")


if __name__ == "__main__":
    main()

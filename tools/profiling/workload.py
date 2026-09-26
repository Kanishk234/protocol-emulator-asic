"""Profile the design-set protocol user designs on generic LUT fabrics.

For every protocol and every fabric variant (LUT3/LUT4/LUT6, with or without half-adder carry
chains), synthesize with Yosys `synth_fabulous` and attribute every LUT to the *function* of the
registers it feeds:

    counter   timing counters and bit/edge counters (candidate primitive: loadable counter/timer)
    shift     shift registers for serial data         (candidate primitive: shift register)
    storage   data held for the host / register maps  (candidate primitive: small register file)
    control   state machines and single-bit flags
    sync      input synchronizers
    pin       registered pin outputs
    config    run-time configuration registers

A LUT is attributed by walking forward through combinational cells to the flip-flops (or output
ports) it drives. A LUT whose output reaches registers of more than one function is counted as
`shared`, never twice. Register -> function is a hand-written table per protocol (`PROTOCOLS`),
reviewed against the RTL; it is the one judgement in the method.

Usage:
    python -m profiling.workload                  # run everything, print tables
    python -m profiling.workload --markdown FILE  # also write the Markdown tables
    python -m profiling.workload --json FILE      # also write the raw numbers
Needs Yosys on PATH (OSS CAD Suite 2026-06-29, docs/VERSIONS.md).
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

FUNCTIONS = ["counter", "shift", "storage", "control", "sync", "pin", "config"]


@dataclass
class Protocol:
    name: str
    top: str
    files: Sequence[str]
    params: Dict[str, int]
    # (regex on the flattened register name, function); first match wins
    roles: Sequence[Tuple[str, str]]
    note: str = ""


PROTOCOLS: List[Protocol] = [
    Protocol(
        "uart", "uart_top",
        ["protocols/uart/uart_tx.v", "protocols/uart/uart_rx.v", "protocols/uart/uart_top.v"],
        {"DIV": 434, "RUNTIME_DIV": 0},
        [(r"cnt$", "counter"), (r"nleft$|nbit$", "counter"),
         (r"u_tx\.shift$|u_rx\.shift$", "shift"),
         (r"u_rx\.sync$", "sync"), (r"u_tx\.tx$", "pin"),
         (r"h_rdata$|u_rx\.data$", "storage"),
         (r"div_q$", "config"),
         (r".*", "control")],
        "115200 baud at 50 MHz, divisor fixed in the bitstream",
    ),
    Protocol(
        "spi_ctrl", "spi_ctrl_top", ["protocols/spi_ctrl/spi_ctrl_top.v"],
        {"CPOL": 0, "CPHA": 0, "HALF": 25},
        [(r"(^|\.)cnt$", "counter"), (r"nedge$", "counter"),
         (r"(^|\.)tx$|(^|\.)rx$", "shift"),
         (r"miso_s$", "sync"), (r"sck_o$|mosi_o$|cs_n_o$", "pin"),
         (r"h_rdata$", "storage"),
         (r".*", "control")],
        "mode 0, SCK = 1 MHz at 50 MHz",
    ),
    Protocol(
        "i2c_ctrl", "i2c_ctrl_top", ["protocols/i2c_ctrl/i2c_ctrl_top.v"],
        {"Q": 125},
        [(r"(^|\.)cnt$", "counter"), (r"nbit$", "counter"),
         (r"out_bits$|in_bits$", "shift"),
         (r"sda_s$|scl_s$", "sync"), (r"sda_oe$|scl_oe$", "pin"),
         (r"h_rdata$", "storage"),
         (r".*", "control")],
        "~100 kHz SCL at 50 MHz",
    ),
    Protocol(
        "i2c_target", "i2c_target_top", ["protocols/i2c_target/i2c_target_top.v"],
        {"NREGS": 4},
        [(r"nbit$", "counter"),
         (r"(^|\.)shift$", "shift"),
         (r"sda_s$|scl_s$", "sync"), (r"sda_oe$", "pin"),
         (r"regs|h_rdata$|dirty$", "storage"),
         (r".*", "control")],
        "4-register map",
    ),
]

VARIANTS = [
    ("LUT3", 3, "none"), ("LUT4", 4, "none"), ("LUT6", 6, "none"),
    ("LUT3+carry", 3, "ha"), ("LUT4+carry", 4, "ha"), ("LUT6+carry", 6, "ha"),
]


def yosys_json(p: Protocol, k: int, carry: str, workdir: str) -> dict:
    out = os.path.join(workdir, f"{p.name}_lut{k}_{carry}.json")
    files = " ".join(os.path.join(ROOT, f) for f in p.files)
    chparams = " ".join(f"-set {n} {v}" for n, v in p.params.items())
    script = (f"read_verilog {files}; chparam {chparams} {p.top}; "
              f"synth_fabulous -top {p.top} -lut {k} -carry {carry}; "
              f"opt_clean -purge; write_json {out}")
    r = subprocess.run(["yosys", "-q", "-p", script], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"yosys failed for {p.name} LUT{k} carry={carry}:\n{r.stderr[-2000:]}")
    with open(out) as f:
        return json.load(f)


def is_ff(cell_type: str) -> bool:
    return cell_type.startswith("LUTFF") or "DFF" in cell_type.upper()


def is_lut(cell_type: str) -> bool:
    return re.fullmatch(r"LUT[1-6]", cell_type) is not None


@dataclass
class Result:
    luts: int = 0
    ffs: int = 0
    other: Counter = field(default_factory=Counter)          # carry cells etc.
    lut_by_fn: Counter = field(default_factory=Counter)      # function or "shared"
    ff_by_fn: Counter = field(default_factory=Counter)
    shared_pairs: Counter = field(default_factory=Counter)   # which functions share LUTs
    unmatched: List[str] = field(default_factory=list)


def analyse(p: Protocol, j: dict) -> Result:
    mod = j["modules"][p.top]
    cells = mod["cells"]
    # bit -> best net name (prefer names without '$')
    names: Dict[int, str] = {}
    for n, info in mod["netnames"].items():
        for bit in info["bits"]:
            if isinstance(bit, int) and (bit not in names or ("$" in names[bit] and "$" not in n)):
                names[bit] = n.lstrip("\\")
    ports_out = {b for pn, pi in mod["ports"].items() if pi["direction"] == "output"
                 for b in pi["bits"] if isinstance(b, int)}

    def role(reg: str) -> str:
        for rx, fn in p.roles:
            if re.search(rx, reg):
                return fn
        return "control"

    res = Result()
    sinks: Dict[int, List[str]] = defaultdict(list)     # bit -> cells reading it
    ff_fn: Dict[str, str] = {}
    comb: List[str] = []
    for cname, c in cells.items():
        t = c["type"]
        dirs = c.get("port_directions", {})
        for pn, bits in c["connections"].items():
            if dirs.get(pn) == "input":
                for b in bits:
                    if isinstance(b, int):
                        sinks[b].append(cname)
        if is_ff(t):
            res.ffs += 1
            q = [b for pn, bits in c["connections"].items() if dirs.get(pn) == "output" for b in bits]
            reg = re.sub(r"\[\d+\]$", "", names.get(q[0], cname)) if q else cname
            fn = role(reg)
            ff_fn[cname] = fn
            res.ff_by_fn[fn] += 1
        else:
            comb.append(cname)
            if is_lut(t):
                res.luts += 1
            else:
                res.other[t] += 1

    memo: Dict[str, frozenset] = {}

    def reach(cname: str, stack=()) -> frozenset:
        """Functions of the registers (or 'pin' for output ports) this comb cell drives."""
        if cname in memo:
            return memo[cname]
        if cname in stack:              # combinational loop guard
            return frozenset()
        c = cells[cname]
        dirs = c.get("port_directions", {})
        fns = set()
        for pn, bits in c["connections"].items():
            if dirs.get(pn) != "output":
                continue
            for b in bits:
                if not isinstance(b, int):
                    continue
                if b in ports_out:
                    fns.add("pin")
                for s in sinks.get(b, []):
                    if s in ff_fn:
                        fns.add(ff_fn[s])
                    else:
                        fns |= reach(s, stack + (cname,))
        memo[cname] = frozenset(fns)
        return memo[cname]

    for cname in comb:
        if not is_lut(cells[cname]["type"]):
            continue
        fns = reach(cname)
        if len(fns) == 1:
            res.lut_by_fn[next(iter(fns))] += 1
        elif not fns:
            res.lut_by_fn["unused"] += 1
        else:
            res.lut_by_fn["shared"] += 1
            res.shared_pairs["+".join(sorted(fns))] += 1
    return res


def run(workdir: str) -> Dict[str, Dict[str, Result]]:
    out: Dict[str, Dict[str, Result]] = {}
    for p in PROTOCOLS:
        out[p.name] = {}
        for label, k, carry in VARIANTS:
            out[p.name][label] = analyse(p, yosys_json(p, k, carry, workdir))
    return out


def tables(results: Dict[str, Dict[str, Result]]) -> str:
    lines = []
    lines.append("### LUTs and flip-flops per fabric variant\n")
    hdr = "| Protocol | " + " | ".join(v[0] for v in VARIANTS) + " | FFs |"
    lines += [hdr, "|" + "---|" * (len(VARIANTS) + 2)]
    for pname, rs in results.items():
        cells = []
        for label, _, _ in VARIANTS:
            r = rs[label]
            extra = f" (+{sum(r.other.values())} carry)" if r.other else ""
            cells.append(f"{r.luts}{extra}")
        lines.append(f"| {pname} | " + " | ".join(cells) + f" | {rs['LUT4'].ffs} |")
    lines.append("")
    lines.append("### LUT4 (no carry): LUTs by the function of the registers they feed\n")
    cols = FUNCTIONS + ["shared", "unused"]
    lines += ["| Protocol | " + " | ".join(cols) + " | total |", "|" + "---|" * (len(cols) + 2)]
    tot = Counter()
    for pname, rs in results.items():
        r = rs["LUT4"]
        tot.update(r.lut_by_fn)
        lines.append(f"| {pname} | " + " | ".join(str(r.lut_by_fn.get(c, 0)) for c in cols) + f" | {r.luts} |")
    lines.append("| **all four** | " + " | ".join(f"**{tot.get(c, 0)}**" for c in cols) + f" | **{sum(tot.values())}** |")
    lines.append("")
    lines.append("### LUT4 (no carry): flip-flops by function\n")
    lines += ["| Protocol | " + " | ".join(FUNCTIONS) + " | total |", "|" + "---|" * (len(FUNCTIONS) + 2)]
    ftot = Counter()
    for pname, rs in results.items():
        r = rs["LUT4"]
        ftot.update(r.ff_by_fn)
        lines.append(f"| {pname} | " + " | ".join(str(r.ff_by_fn.get(c, 0)) for c in FUNCTIONS) + f" | {r.ffs} |")
    lines.append("| **all four** | " + " | ".join(f"**{ftot.get(c, 0)}**" for c in FUNCTIONS) + f" | **{sum(ftot.values())}** |")
    lines.append("")
    lines.append("### LUT4: LUTs shared between functions\n")
    lines += ["| Protocol | shared between | LUTs |", "|---|---|---|"]
    for pname, rs in results.items():
        for pair, n in rs["LUT4"].shared_pairs.most_common():
            lines.append(f"| {pname} | {pair} | {n} |")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--markdown")
    ap.add_argument("--json")
    ap.add_argument("--workdir")
    a = ap.parse_args(argv)
    wd = a.workdir or tempfile.mkdtemp(prefix="warp_profile_")
    os.makedirs(wd, exist_ok=True)
    results = run(wd)
    md = tables(results)
    print(md)
    if a.markdown:
        with open(a.markdown, "w") as f:
            f.write(md)
    if a.json:
        with open(a.json, "w") as f:
            json.dump({p: {v: {"luts": r.luts, "ffs": r.ffs, "other": dict(r.other),
                                "lut_by_fn": dict(r.lut_by_fn), "ff_by_fn": dict(r.ff_by_fn),
                                "shared": dict(r.shared_pairs)}
                           for v, r in rs.items()} for p, rs in results.items()}, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())

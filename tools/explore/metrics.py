"""Architecture metrics over every shipped program (ISA.md §9, PHASE1 §2.0).

For each `programs/*.trw`: slots per lane, registers and K constants used, routines (words, worst
case), SRAM, and how often each D-007 feature is used, with a static lower bound on the slots a
program would need without it:
- head-bit tests (HE/HV, HS): each use needs one more slot to put the bit into a flag first;
- flags from non-compare ops (D-007 "a flag from every op"): each use needs one more compare slot;
- K constants: without K, every distinct K value must live in a free register (16-bit values do
  not fit the 8-bit immediate); if there are not enough free registers the program needs routines
  or more slots (reported as "no fit");
- implicit readiness checks (inputs available / outputs free): every slot that reads I0/I1 or
  writes O0/O1 would need explicit conditions the slot format does not have (so: not removable).

Usage: python -m explore.metrics  (from tools/), prints Markdown.
"""

import pathlib

import tripc
import tripwire_spec as S
from tripsim import isa

PROGRAMS = pathlib.Path(__file__).resolve().parents[2] / "programs"
COMPARES = {S.OPS["CMPM"], S.OPS["LTU"], S.OPS["PAR"]}
IN_SRC = {S.ASRC["I0"], S.ASRC["I1"]}
OUT_DST = {S.DST["O0"], S.DST["O1"]}
REG_SRC = {S.ASRC[f"r{i}"] for i in range(4)}
REG_DST = {S.DST[f"r{i}"] for i in range(4)}


def lane_metrics(lane, image):
    slots = [isa.decode_slot(int(w, 16)) for w in lane["slots"]]
    regs, ks, head, flagops, ready = set(), set(), 0, 0, 0
    for s in slots:
        if s.ASRC in REG_SRC:
            regs.add(s.ASRC)
        if s.DST in REG_DST:
            regs.add(s.DST)
        if s.BSEL == S.BSEL["reg"] and s.OP not in (S.OPS["CALL"], S.OPS["CMPM"]):
            regs.add(s.IMM & 3)
        if s.BSEL == S.BSEL["k"]:
            ks.add(s.IMM & 3)
        if s.OP == S.OPS["CMPM"] and (s.IMM >> 4) & 1:
            ks.update({s.IMM & 3, (s.IMM >> 2) & 3})
        head += s.HE
        flagops += int(s.DFE and s.DF != 3 and s.OP not in COMPARES)
        ready += int(s.ASRC in IN_SRC or s.DST in OUT_DST or s.OP == S.OPS["CALL"])
    return {"slots": len(slots), "regs": len(regs), "k": len(ks), "head": head,
            "flagops": flagops, "ready": ready}


def program_metrics(path):
    image, _ = tripc.compile_file(path)
    lanes = {name: lane_metrics(l, image) for name, l in image["lanes"].items()}
    routines = image["routines"]
    return {
        "name": path.stem, "lanes": lanes,
        "routines": len(routines),
        "max_steps": max((r["max_steps"] or 0 for r in routines.values()), default=0),
        "sram": len(image["sram"]),
        "units": len(image["pins"]),
    }


def ablation(lm):
    """Estimated slots without each feature (lower bounds) for one lane."""
    free_regs = 4 - lm["regs"]
    return {
        "head": lm["slots"] + lm["head"],
        "flags": lm["slots"] + lm["flagops"],
        "k": "fits" if lm["k"] <= free_regs else "no fit",
    }


def main():
    rows = [program_metrics(p) for p in sorted(PROGRAMS.glob("*.trw"))]
    print("| Program | Lane | Slots | Regs | K | Head tests | Flags from ALU ops | Ready-dependent slots"
          " | Slots w/o head tests | Slots w/o ALU flags | K in free regs? | Routines (max steps) | SRAM | Units |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    over = {"head": [], "flags": [], "k": []}
    for r in rows:
        for i, (name, lm) in enumerate(sorted(r["lanes"].items())):
            ab = ablation(lm)
            for key, bad in (("head", ab["head"] > 12), ("flags", ab["flags"] > 12), ("k", ab["k"] == "no fit")):
                if bad:
                    over[key].append(f"{r['name']}.{name}")
            tail = (f"{r['routines']} ({r['max_steps']}) | {r['sram']} | {r['units']} |" if i == 0 else "| | |")
            print(f"| {r['name'] if i == 0 else ''} | {name} | {lm['slots']} | {lm['regs']} | {lm['k']} | "
                  f"{lm['head']} | {lm['flagops']} | {lm['ready']} | {ab['head']} | {ab['flags']} | {ab['k']} | {tail}")
    print()
    for key, label in (("head", "head-bit tests"), ("flags", "flags from ALU ops"), ("k", "K constants")):
        print(f"- Without {label}, lanes that no longer fit 12 slots / 4 registers: "
              f"{', '.join(over[key]) or 'none'}.")


if __name__ == "__main__":
    main()

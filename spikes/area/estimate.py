"""Area estimate, step 2 (phase 2 task 2.0): building-block areas x counts per chip block.

Reads build/prims.tsv (from run_area.sh), the pin configuration layout from the generated spec
tables, and every program in programs/ (through tripc) to see which pin-unit features programs
use and on how many units at once. Prints the tables for docs/reports/AREA_ESTIMATE.md.

    source .venv/bin/activate && python spikes/area/estimate.py
"""

import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import tripc                      # noqa: E402
import tripwire_spec as S         # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
P = {r["label"]: float(r["area_um2"]) for r in csv.DictReader(open(HERE / "build/prims.tsv"), delimiter="\t")}

CORE = 902_417          # 6x4 core, µm² (AREA.md row 1)
SRAM = 45_309           # 512x16 macro (AREA.md row 2); does not grow in layout
LAYOUT = 1.30           # std-cell growth from Yosys to placed-and-routed (R2: ~79K -> 103K)
GLUE = (0.30, 0.45, 0.60)   # control logic (FSMs, op decode, mode muxes, flags) as a share of datapath
CFG_FLOP = 73.4         # µm² per host-written bit in flops (ae_cfg: 25,833 / 352)
CFG_LATCH = 35.1        # µm² per bit in a latch array with clock gates (R1 slots: 24,549 / 700)
FLOP = 49.0             # one plain flop (dfrbpq_1)

# R1 lane, Yosys (R1_LANE_TIMING.md §4): lane + ALU + latch slots + 2 consumer ports
LANE = 65_400
LANE_READPORT = 9_350

# --- pin-unit features: configuration fields and datapath blocks -----------------------------
FEATURES = {
    "core": dict(
        fields="txmode rxmode order od idle autorearm rx_echo tx_lentok tx_preload stretch pin_a pin_b "
               "rx_edge tx_edge ev_pin ev_edge ev_qual ev_reset period presc sampleofs nbits "
               "rx_nbits rx_nbits2".split(),
        blocks={"timer24": 2, "cursor": 1, "txshift": 1, "rxframe": 1, "padsel": 2, "event": 1,
                "prod": 1, "port7": 1}),
    "pins C/S/N": dict(
        fields="pin_c c_active c_oe pin_s pin_n".split(),
        blocks={"padsel": 2}),
    "PULSE": dict(
        fields="sym0_t1 sym0_first sym0_t2 sym1_t1 sym1_first sym1_t2".split(),
        blocks={"pulse": 1}),
    "carrier": dict(
        fields=["carrier"],
        blocks={"timer24": 1}),
    "BITSYNC": dict(
        fields="nrzi oe_auto sjw idle_bits resync delim stuff_n stuff_lvl crc_width crc_skip "
               "crc_poly crc_init crc_res crc_xor".split(),
        blocks={"crc16": 2, "bitsync_ctl": 1}),
}


def cfg_bits(fields):
    return sum(S.PIN_CFG_FIELDS[f][1] for f in fields)


def check_fields():
    named = {f for ft in FEATURES.values() for f in ft["fields"]}
    assert named == set(S.PIN_CFG_FIELDS), set(S.PIN_CFG_FIELDS) ^ named


def feature_area(name, glue, cfg_per_bit):
    ft = FEATURES[name]
    dp = sum(P[b] * n for b, n in ft["blocks"].items())
    return dp, dp * glue, cfg_bits(ft["fields"]) * cfg_per_bit


def unit_area(features, glue, cfg_per_bit):
    return sum(sum(feature_area(f, glue, cfg_per_bit)) for f in features)


# --- which features the programs use, per unit --------------------------------------------
def feature_use():
    rows = []
    for path in sorted((ROOT / "programs").glob("*.trw")):
        image, _ = tripc.compile_file(path)
        units = image["pins"]
        use = {"units": len(units), "PULSE": 0, "carrier": 0, "BITSYNC": 0, "pins C/S/N": 0}
        for cfg in units.values():
            if cfg.get("txmode") == "pulse":
                use["PULSE"] += 1
            if cfg.get("carrier", 0):
                use["carrier"] += 1
            if cfg.get("txmode") == "bitsync" or cfg.get("rxmode") == "bitsync":
                use["BITSYNC"] += 1
            if any(cfg.get(k) is not None for k in ("pin_c", "pin_s", "pin_n")):
                use["pins C/S/N"] += 1
        rows.append((path.stem, use))
    return rows


def other_blocks():
    """Everything outside lanes and pin units (Yosys µm², before layout)."""
    fabric = 7 * P["prod"] + P["port8"] + 13 * 10 * CFG_FLOP + 13 * 200   # lane/host producers,
    #   HOST_OUT port, sel/en/mode/accept of 13 ports, release terms (estimate)
    pins = 14 * P["padout"] + 48 * CFG_FLOP + 19 * 2 * FLOP               # pad drivers, owners, 2-FF syncs
    host = P["spi"] + P["rdmux48"] + 64 * FLOP + 3_000                    # SPI, lane-register read-back,
    #   control/status registers, decode (estimate)
    misc = 16 * FLOP + 400 + 2_000                                        # time base, SRAM rotation/wrapper
    return {"fabric (outside lanes and units)": fabric, "pad drivers, owners, synchronisers": pins,
            "host interface": host, "time base, SRAM wrapper": misc}


def chip(unit_mix, glue, cfg_per_bit, lanes=3, readport=False, cfg_readback=False):
    lanes_a = lanes * (LANE + (LANE_READPORT if readport else 0))
    units_a = sum(n * unit_area(f, glue, cfg_per_bit) for n, f in unit_mix)
    oth = sum(other_blocks().values())
    if cfg_readback:
        oth += P["rdmux22"] * 6
    logic = lanes_a + units_a + oth
    placed = logic * LAYOUT + SRAM
    return lanes_a, units_a, oth, logic, placed, placed / CORE


ALL = list(FEATURES)
LEAN = ["core", "pins C/S/N"]


def fmt(x):
    return f"{x / 1000:,.1f}K"


def main():
    check_fields()
    print("## Building blocks (Yosys, cmos5l typ, before layout)\n")
    print("| Block | µm² |\n|---|---|")
    for k, v in P.items():
        print(f"| {k} | {v:,.0f} |")

    print("\n## Pin unit by feature (glue at 45 %)\n")
    print("| Feature | Config bits | Datapath | Glue | Config (flops) | Config (latches) | Total (flops) | Total (latches) |")
    print("|---|---|---|---|---|---|---|---|")
    for f in FEATURES:
        dp, gl, cf = feature_area(f, GLUE[1], CFG_FLOP)
        _, _, cl = feature_area(f, GLUE[1], CFG_LATCH)
        print(f"| {f} | {cfg_bits(FEATURES[f]['fields'])} | {fmt(dp)} | {fmt(gl)} | {fmt(cf)} | {fmt(cl)} "
              f"| {fmt(dp + gl + cf)} | {fmt(dp + gl + cl)} |")
    print(f"| **full unit** | {cfg_bits([x for f in FEATURES.values() for x in f['fields']])} | | | | "
          f"| **{fmt(unit_area(ALL, GLUE[1], CFG_FLOP))}** | **{fmt(unit_area(ALL, GLUE[1], CFG_LATCH))}** |")

    print("\n## Feature use in programs/ (units per program)\n")
    use = feature_use()
    print("| Program | Units | PULSE | carrier | BITSYNC | pins C/S/N |\n|---|---|---|---|---|---|")
    for name, u in use:
        print(f"| {name} | {u['units']} | {u['PULSE']} | {u['carrier']} | {u['BITSYNC']} | {u['pins C/S/N']} |")
    mx = {k: max(u[k] for _, u in use) for k in ("units", "PULSE", "carrier", "BITSYNC", "pins C/S/N")}
    print(f"| **max at once** | {mx['units']} | {mx['PULSE']} | {mx['carrier']} | {mx['BITSYNC']} | {mx['pins C/S/N']} |")

    print("\n## Other blocks (before layout)\n")
    for k, v in other_blocks().items():
        print(f"- {k}: {fmt(v)}")

    print("\n## Whole chip (placed = Yosys x 1.30 + SRAM macro; core 902K µm²)\n")
    print("| Scenario | Lanes | Pin units | Other | Placed (glue 30 / 45 / 60 %) | Utilisation |")
    print("|---|---|---|---|---|---|")
    scen = [
        ("A. spec as frozen: 6 full units, config in flops", [(6, ALL)], CFG_FLOP, {}),
        ("B. A + slot and config read-back", [(6, ALL)], CFG_FLOP, dict(readport=True, cfg_readback=True)),
        ("C. 6 full units, config in latches", [(6, ALL)], CFG_LATCH, {}),
        ("D. 2 full + 4 lean units, config in flops", [(2, ALL), (4, LEAN)], CFG_FLOP, {}),
        ("E. 2 full + 4 lean units, config in latches", [(2, ALL), (4, LEAN)], CFG_LATCH, {}),
        ("F. E with 2 lanes", [(2, ALL), (4, LEAN)], CFG_LATCH, dict(lanes=2)),
        ("G. 4 units (2 full + 2 lean), config in latches", [(2, ALL), (2, LEAN)], CFG_LATCH, {}),
        ("H. G with 2 lanes", [(2, ALL), (2, LEAN)], CFG_LATCH, dict(lanes=2)),
    ]
    for label, mix, cpb, kw in scen:
        res = [chip(mix, g, cpb, **kw) for g in GLUE]
        la, ua, ot, _, _, _ = res[1]
        pl = " / ".join(fmt(r[4]) for r in res)
        ut = " / ".join(f"{r[5] * 100:.0f} %" for r in res)
        print(f"| {label} | {fmt(la)} | {fmt(ua)} | {fmt(ot)} | {pl} | {ut} |")


if __name__ == "__main__":
    main()

"""L0-GEN: the spec validates, catches malformed specs, and every generated output is current."""

import copy
import re
import subprocess
import sys

import pytest
import yaml

from gen import gen

SPEC = yaml.safe_load(gen.SPEC.read_text())


def test_spec_is_valid():
    gen.validate(SPEC)


def test_generated_outputs_are_current():
    """The same check CI runs: regenerating changes nothing."""
    for rel, content in gen.outputs(SPEC).items():
        assert (gen.ROOT / rel).read_text() == content, f"{rel} is out of date: run tools/gen/gen.py"


def test_check_mode_exit_code():
    r = subprocess.run([sys.executable, str(gen.ROOT / "tools/gen/gen.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def broken(mutate):
    s = copy.deepcopy(SPEC)
    mutate(s)
    return s


def field(s, name):
    return next(f for f in s["slot"]["fields"] if f["name"] == name)


@pytest.mark.parametrize("label, mutate", [
    ("overlapping slot fields", lambda s: field(s, "HS").__setitem__("lsb", 51)),
    ("slot bits left unused", lambda s: s["slot"].__setitem__("bits", 54)),
    ("slot wider than host words", lambda s: s["slot"].__setitem__("host_words", 3)),
    ("duplicate op code", lambda s: s["ops"][1].__setitem__("code", 0)),
    ("enum value too wide", lambda s: s["slot"]["enums"]["DST"].__setitem__("none", 8)),
    ("duplicate tag", lambda s: s["token"]["tags"][1].__setitem__("code", 0)),
    ("routine field overlaps sub", lambda s: s["routine"]["ctrl"]["formats"][0]["fields"].__setitem__("imm", [12, 0])),
    ("YAML boolean key (bare off)", lambda s: s["routine"]["ctrl"]["formats"][2]["fields"].__setitem__(False, [8, 0])),
    ("duplicate pin command", lambda s: s["pin_commands"][1].__setitem__("code", 1)),
    ("signed field missing", lambda s: s["routine"]["ctrl"]["formats"][2].__setitem__("signed", ["nope"])),
    ("fabric port over its sel bits", lambda s: s["fabric"].__setitem__("sel_bits", 3)),
    ("fabric source listed twice", lambda s: s["fabric"]["sources"]["HOST_OUT"].append("U0.rx")),
    ("fabric bad source pattern", lambda s: s["fabric"]["sources"]["HOST_OUT"].append("CRC")),
    ("unknown host pad", lambda s: s["pads"]["host"].__setitem__(3, "uo9")),
    ("pin config fields overlap", lambda s: s["pin_config"]["fields"][1].__setitem__("bit", 2)),
    ("pin config field crosses a word", lambda s: s["pin_config"]["fields"][0].__setitem__("bit", 14)),
    ("pin config pad not 5 bits", lambda s: next(f for f in s["pin_config"]["fields"] if f["kind"] == "pad").__setitem__("width", 4)),
    ("pin config enum too wide", lambda s: s["pin_config"]["fields"][0]["values"].__setitem__("x", 8)),
    ("pin config outside the block", lambda s: s["pin_config"].__setitem__("stride", 16)),
    ("pin feature with an unknown field", lambda s: s["pin_config"]["features"]["carrier"]["fields"].append("nope")),
    ("pin field in two features", lambda s: s["pin_config"]["features"]["carrier"]["fields"].append("crc_poly")),
    ("pin feature with an unknown mode", lambda s: s["pin_config"]["features"]["pulse"]["modes"]["txmode"].append("x")),
    ("pin units not one per unit", lambda s: s["pin_config"]["units"].pop()),
    ("pin unit with an unknown feature", lambda s: s["pin_config"]["units"][2].append("usb")),
    ("pin config storage", lambda s: s["pin_config"].__setitem__("storage", "sram")),
])
def test_validation_catches(label, mutate):
    with pytest.raises(gen.SpecError):
        gen.validate(broken(mutate))


def test_legal_sources_expand_per_lane():
    ls = gen.legal_sources(SPEC["fabric"])
    assert ls["L0.I1"][-2:] == ("L1.O0", "L2.O1") and ls["L2.I1"][-2:] == ("L0.O0", "L1.O1")
    assert len(ls["L1.I1"]) == 9 and max(len(v) for k, v in ls.items() if not k.endswith("I1")) == 8


def test_a_spec_change_reaches_every_output():
    """Renumbering one op changes the Python tables, the Verilog defines and the ISA doc."""
    def swap(s):
        s["ops"][0]["code"], s["ops"][1]["code"] = 1, 0
    new = gen.outputs(broken(swap))
    cur = gen.outputs(SPEC)
    for rel in ("tools/tripwire_spec.py", "src/trw_defs.vh", "docs/design/ISA.md"):
        assert new[rel] != cur[rel], rel


def test_model_uses_the_spec():
    """tripsim's encodings are the generated ones, not a private copy."""
    import tripwire_spec as S
    from tripsim import isa
    assert isa.SLOT_FIELDS == S.SLOT_FIELDS and isa.SLOT_BITS == S.SLOT_BITS
    assert isa.OP == S.OPS and isa.TAGS == S.TAGS


def _defines(text):
    """`define NAME value lines of a generated Verilog header, as {NAME: value string}."""
    return dict(m.groups() for m in re.finditer(r"^`define (\w+) (\S+)$", text, re.M))


def _vint(v):
    """A Verilog literal such as 5'd31, 352'h00ff or 6'b000011, as an int."""
    if "'" not in v:
        return int(v)
    base, digits = v.split("'")[1][0], v.split("'")[1][1:]
    return int(digits, {"d": 10, "h": 16, "b": 2}[base])


def test_verilog_pin_config_matches_the_spec():
    """The RTL takes §7.2 positions from src/trw_defs.vh; every field, enum code and stored-bit mask
    there is the spec's (the RTL's source for trw_pin_cfg.v / trw_pin_unit.v, not a hand copy)."""
    d = _defines(gen.gen_verilog(SPEC))
    pc = SPEC["pin_config"]
    for f in pc["fields"]:
        n = f["name"].upper()
        assert _vint(d[f"TRW_PC_{n}_LSB"]) == f["bit"]
        assert _vint(d[f"TRW_PC_{n}_W"]) == f["width"]
        assert _vint(d[f"TRW_PC_{n}_MSB"]) == f["bit"] + f["width"] - 1
        for k, v in f.get("values", {}).items():
            assert _vint(d[f"TRW_PCE_{n}_{str(k).upper()}"]) == v
    assert _vint(d["TRW_PC_WORDS"]) == 22 and _vint(d["TRW_PC_BITS"]) == 352
    core = _vint(d["TRW_PC_MASK_CORE"])
    opt = {k: _vint(d[f"TRW_PC_MASK_{k.upper()}"]) for k in pc["features"]}
    # D-036/D-040: 307 bits in a full unit, of which the lean units keep the core
    assert bin(core).count("1") + sum(bin(m).count("1") for m in opt.values()) == 307
    assert bin(core).count("1") == 119
    for feat, m in opt.items():
        assert not m & core
        want = 0
        for f in pc["fields"]:
            if f["name"] in pc["features"][feat]["fields"]:
                want |= ((1 << f["width"]) - 1) << f["bit"]
        assert m == want, feat
        units = _vint(d[f"TRW_PC_UNITS_{feat.upper()}"])
        assert units == sum(1 << u for u, fs in enumerate(pc["units"]) if feat in fs)


def test_verilog_pin_masks_follow_a_feature_change():
    """Moving a field into a feature moves its bits out of the core mask."""
    s = broken(lambda s: s["pin_config"]["features"]["carrier"]["fields"].append("stretch"))
    d = _defines(gen.gen_verilog(s))
    bit = next(f["bit"] for f in SPEC["pin_config"]["fields"] if f["name"] == "stretch")
    assert not _vint(d["TRW_PC_MASK_CORE"]) >> bit & 1
    assert _vint(d["TRW_PC_MASK_CARRIER"]) >> bit & 1


def test_colliding_verilog_defines_are_rejected():
    """Two spec names that map to one `define (here DST 'o0' next to 'O0') fail instead of shadowing."""
    s = broken(lambda s: s["slot"]["enums"]["DST"].__setitem__("o0", 7))
    with pytest.raises(gen.SpecError, match="TRW_DST_O0"):
        gen.gen_verilog(s)

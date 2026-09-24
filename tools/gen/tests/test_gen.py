"""L0-GEN: the spec validates, catches malformed specs, and every generated output is current."""

import copy
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

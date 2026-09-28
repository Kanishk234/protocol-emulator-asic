"""Pin-unit configuration registers (ARCHITECTURE.md §7.2, D-036)."""

import dataclasses

import pytest

import tripc
import tripwire_spec as S
from kernels import PROGRAMS
from tripsim import Chip, pinregs
from tripsim.pinunit import PinConfig


def test_layout_covers_exactly_the_model_settings():
    assert pinregs.check_fields() == set()


def test_every_program_round_trips_exactly():
    for path in sorted(PROGRAMS.glob("*.trw")):
        image, _ = tripc.compile_file(path)
        for unit, cfg in image["pins"].items():
            u = int(unit[1:])
            words = pinregs.encode(PinConfig(**cfg), u)
            assert [f"{w:04x}" for w in words] == image["pin_regs"][unit]
            back = pinregs.decode(words, u)
            assert pinregs.encode(back, u) == words, (path.stem, unit)
            orig = PinConfig(**cfg)
            # the quantities the model computes with are identical after the round trip
            assert back.period_q8 == orig.period_q8
            assert round(back.sampleofs * back.period_q8) == round(orig.sampleofs * orig.period_q8)
            assert round(back.carrier * 256) == round(orig.carrier * 256)
            assert round(back.sjw * 256) == round(orig.sjw * 256)
            for f in dataclasses.fields(PinConfig):
                if f.name not in ("period", "sampleofs", "carrier", "sjw"):
                    assert getattr(back, f.name) == getattr(orig, f.name), (path.stem, unit, f.name)


def test_known_encoding():
    words = pinregs.encode(PinConfig(pin_a=8, txmode="shift", period=433.75, presc=50, nbits=10,
                                     sampleofs=0.5, idle=1))
    assert words[0] & 0x7 == 1 and (words[0] >> 7) & 1 == 1           # SHIFT, IDLE 1
    assert words[1] & 0x1F == 8 and (words[1] >> 5) & 0x1F == 31      # pin A = uo0, pin B none
    assert words[4] | (words[5] & 0xFF) << 16 == 433 * 256 + 192      # PERIOD 16.8
    assert words[5] >> 8 == 49                                         # PRESC - 1
    assert words[6] | (words[7] & 0xFF) << 16 == round(0.5 * (433 * 256 + 192))
    assert (words[7] >> 8) & 0xF == 9                                  # NBITS - 1
    base, stride = S.PIN_CFG_BASE, S.PIN_CFG_STRIDE
    assert base + len(S.PIN_UNIT_FEATURES) * stride <= S.PIN_OWNER_BASE


@pytest.mark.parametrize("bad", [dict(period=70000), dict(presc=300), dict(nbits=17),
                                 dict(crc_skip=40), dict(idle_bits=32), dict(txmode="nope"),
                                 dict(sym0_t1=4096)])
def test_values_that_do_not_fit_are_rejected(bad):
    with pytest.raises(ValueError):
        pinregs.encode(PinConfig(**bad))


def test_units_follow_the_spec():
    """D-040: each unit stores exactly its generated optional-feature set."""
    assert [set(pinregs.features(u)) for u in range(len(S.PIN_UNIT_FEATURES))] == [
        set(features) for features in S.PIN_UNIT_FEATURES]


def test_chip_default_lane_and_unit_counts_follow_generated_spec(monkeypatch):
    # Exercise a smaller generated shape so hard-coded 3/6 defaults cannot pass.
    monkeypatch.setattr(S, "LEGAL_SOURCES", {"L0.I0": (), "L1.I0": ()})
    monkeypatch.setattr(S, "PIN_UNIT_FEATURES", ((), (), (), ()))
    chip = Chip()
    assert len(chip.lanes) == 2
    assert len(chip.pins) == 4


def test_lean_units_do_not_store_optional_fields():
    """D-040: on U2-U5 the PULSE, carrier and BITSYNC field bits are never set, and read as defaults."""
    opt = {f for fields, _ in S.PIN_FEATURES.values() for f in fields}
    full = PinConfig(pin_a=8, period=10.5, idle_bits=11, sym0_first=1, crc_poly=0x1021, carrier=3.0)
    lean = [u for u, features in enumerate(S.PIN_UNIT_FEATURES) if not features]
    for u in lean:
        cfg = PinConfig(pin_a=8, period=10.5)
        words = pinregs.encode(cfg, u)
        for name in opt:
            bit, width, _ = S.PIN_CFG_FIELDS[name]
            assert not any(words[(bit + i) // 16] >> ((bit + i) % 16) & 1 for i in range(width)), name
        assert pinregs.decode(words, u) == cfg
    words = pinregs.encode(full, 0)
    assert pinregs.decode(words, 0).crc_poly == 0x1021 and pinregs.decode(words, 0).carrier == 3.0


@pytest.mark.parametrize("bad, feature", [
    (dict(txmode="pulse"), "PULSE"), (dict(sym1_t2=5), "PULSE"),
    (dict(carrier=2.0), "CARRIER"),
    (dict(txmode="bitsync", rxmode="bitsync"), "BITSYNC"), (dict(crc_width=8), "BITSYNC"),
])
def test_lean_unit_rejects_optional_features(bad, feature):
    full = [u for u, features in enumerate(S.PIN_UNIT_FEATURES) if set(S.PIN_FEATURES) <= set(features)]
    lean = [u for u, features in enumerate(S.PIN_UNIT_FEATURES) if feature.lower() not in features]
    for u in full:
        pinregs.encode(PinConfig(**bad), u)
    target = lean[0]
    with pytest.raises(ValueError, match=f"U{target} has no {feature}"):
        pinregs.encode(PinConfig(**bad), target)
    chip = Chip()
    with pytest.raises(ValueError, match=f"U{target} has no {feature}"):
        chip.pin_config(target, **bad)
    chip.pin_config(full[0], **bad)


def test_tripc_rejects_a_feature_on_a_lean_unit():
    lean = next(u for u, features in enumerate(S.PIN_UNIT_FEATURES) if "pulse" not in features)
    with pytest.raises(tripc.TrwError, match=f"U{lean} has no PULSE"):
        tripc.compile_text(f"program t\npin U{lean}: pin_a=uo0 txmode=pulse\n")


def test_tripc_reports_a_value_that_does_not_fit():
    with pytest.raises(tripc.TrwError, match="U0: pin config presc"):
        tripc.compile_text("program t\npin U0: pin_a=uo0 presc=300\n")

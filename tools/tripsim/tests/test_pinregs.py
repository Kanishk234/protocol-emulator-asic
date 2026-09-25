"""Pin-unit configuration registers (ARCHITECTURE.md §7.2, D-036)."""

import dataclasses

import pytest

import tripc
import tripwire_spec as S
from kernels import PROGRAMS
from tripsim import pinregs
from tripsim.pinunit import PinConfig


def test_layout_covers_exactly_the_model_settings():
    assert pinregs.check_fields() == set()


def test_every_program_round_trips_exactly():
    for path in sorted(PROGRAMS.glob("*.trw")):
        image, _ = tripc.compile_file(path)
        for unit, cfg in image["pins"].items():
            words = pinregs.encode(PinConfig(**cfg))
            assert [f"{w:04x}" for w in words] == image["pin_regs"][unit]
            back = pinregs.decode(words)
            assert pinregs.encode(back) == words, (path.stem, unit)
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
    assert base + 6 * stride <= S.PIN_OWNER_BASE


@pytest.mark.parametrize("bad", [dict(period=70000), dict(presc=300), dict(nbits=17),
                                 dict(crc_skip=40), dict(idle_bits=32), dict(txmode="nope"),
                                 dict(sym0_t1=4096)])
def test_values_that_do_not_fit_are_rejected(bad):
    with pytest.raises(ValueError):
        pinregs.encode(PinConfig(**bad))


def test_tripc_reports_a_value_that_does_not_fit():
    with pytest.raises(tripc.TrwError, match="U0: pin config presc"):
        tripc.compile_text("program t\npin U0: pin_a=uo0 presc=300\n")

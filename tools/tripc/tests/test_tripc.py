"""tripc v0: compiled programs match the reference kernels bit for bit; static checks fire."""

import pytest

import tripc
from kernels import PROGRAMS, i2c_controller, i2c_target, spi_controller, spi_target
from tripsim.asm import link_routines


def compiled(name, **params):
    image, report = tripc.compile_file(PROGRAMS / f"{name}.trw", params)
    return image, report


def slots(image, lane="L0"):
    return [int(w, 16) for w in image["lanes"][lane]["slots"]]


@pytest.mark.parametrize("name, params, ref_slots, ref_k", [
    ("i2c_target", {"ADDR": 0x50}, i2c_target.slots(), [0x00FE, 0x50 << 1, 0x7000, 0]),
    ("i2c_target", {"ADDR": 0x2A}, i2c_target.slots(), [0x00FE, 0x2A << 1, 0x7000, 0]),
    ("spi_controller", {}, spi_controller.slots(), [0x3008, 0, 0, 0]),
    ("spi_target", {}, spi_target.slots(), [0x7000, 0, 0, 0]),
    ("i2c_controller", {"PERIOD": 124}, i2c_controller.slots(),
     [i2c_controller.LEVEL0, i2c_controller.LEN8, i2c_controller.CLK9, i2c_controller.CLK8]),
])
def test_compiled_slots_match_reference_kernels(name, params, ref_slots, ref_k):
    image, _ = compiled(name, **params)
    assert slots(image) == ref_slots
    assert image["lanes"]["L0"]["k"] == ref_k


@pytest.mark.parametrize("period", [50, 124, 500])
def test_compiled_routines_match_reference(period):
    image, _ = compiled("i2c_controller", PERIOD=period)
    assert image["sram"] == link_routines(i2c_controller.routines(period))
    assert image["lanes"]["L0"]["regs"][0] == 1


def test_reports_and_slot_budget():
    for p in PROGRAMS.glob("*.trw"):
        image, report = tripc.compile_file(p)
        assert f"# tripc report: {image['program']}" in report
        assert all(len(l["slots"]) <= 12 for l in image["lanes"].values())
        assert "Warnings" not in report, report       # every shipped routine has a static bound


def errors(src):
    with pytest.raises(tripc.TrwError) as e:
        tripc.compile_text("program t\n" + src)
    return str(e.value)


@pytest.mark.parametrize("src, needle", [
    ("lane L0:\n    slot: when NOPE do MOV r0 <- zero\n", "unknown condition"),
    ("lane L0:\n    states A\n    slot: when A do MOV r0 <- zero then B\n", "unknown state"),
    ("lane L0:\n    slot: when I1 is DATA do MOV O0 <- I0, deq\n", "condition tests I1"),
    ("lane L0:\n    slot: when head15 == 1 do MOV O0 <- r0\n", "head-bit tests need"),
    ("lane L0:\n    slot: do ADD r0 <- r0, 1 -> f3\n", "read-only"),
    ("lane L0:\n    K0 = 0x10000\n", "16-bit"),
    ("lane L0:\n" + "    slot: do ADD r0 <- r0, 1\n" * 13, "more than 12"),
    ("pin U0: pin_a=ui4\n", "host port"),
    ("pin U0: pin_a=uio9\n", "unknown pad"),
    ("pin U0: bogus=1\n", "unknown pin setting"),
    ("connect L0.I0 <- HOST_IN accept=NOPE\n", "unknown tag"),
    ("lane L0:\n    slot: do CALL missing\n", "CALL needs a defined routine"),
    ("lane L0:\n    slot: do FOO r0 <- zero\n", "unknown operation"),
])
def test_static_checks(src, needle):
    assert needle in errors(src)


def test_error_carries_line_number():
    msg = errors("lane L0:\n    states A\n    slot: when A do MOV r0 <- zero then B\n")
    assert ":4:" in msg


def test_routine_bounds():
    src = """program t
routine loop:
    ldi r0, 10
  top:
    ADD r1, r1, 1
    djnz r0, top
    ret
routine free:
  top:
    ADD r1, r1, 1
    br top
lane L0:
    slot: do CALL loop
"""
    image, report = tripc.compile_text(src)
    assert image["routines"]["loop"]["max_steps"] == 1 + 2 * 10 + 1
    assert image["routines"]["free"]["max_steps"] is None
    assert "no static bound" in report


def test_routine_bound_is_the_longest_path_not_the_first_ret():
    """BUGS #17: an early RET must not hide a longer path."""
    src = """program t
routine early:
    add r1, r1, 0
    br long if nrz
    ret
  long:
    add r1, r1, 1
    add r1, r1, 1
    add r1, r1, 1
    ld r2, r1, 0
    ret
lane L0:
    slot: do CALL early
"""
    image, _ = tripc.compile_text(src)
    assert image["routines"]["early"]["max_steps"] == 2 + 3 + 2 + 1


def test_params_override_and_unknown():
    image, _ = compiled("uart", BAUD=1_000_000)
    assert image["pins"]["U0"]["period"] == 50.0
    with pytest.raises(tripc.TrwError, match="unknown params"):
        compiled("uart", NOPE=1)


def test_ld_st_offset_is_a_whole_expression():
    """BUGS #22: `ld r2, r3, BASE + 1` used to load BASE (the rest was dropped)."""
    src = """program t
const BASE = 16
routine r:
    ld r2, r3, BASE + 1
    st r2, r3, BASE * 2 + 3
    ret
lane L0:
    slot: do CALL r
"""
    image, _ = tripc.compile_text(src)
    from tripsim import isa
    words = image["sram"][32:35]
    assert isa.decode_routine(words[0])["off"] == 17
    assert isa.decode_routine(words[1])["off"] == 35

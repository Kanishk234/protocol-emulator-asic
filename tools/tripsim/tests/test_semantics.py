"""ARCHITECTURE.md §14 rules pinned by the second-person review (DECISIONS D-035).

One test per rule that no other test pins down, plus regressions for BUGS #35-#39.
A few tests set lane or pin-unit state directly, to hit an exact same-clock case.
"""

import pytest

import tripwire_spec as S
from tripsim import PAD_UI, PAD_UIO, PAD_UO, Chip, pinregs
from tripsim.pinunit import PinConfig
from tripsim.asm import Routine, link_routines, reflex

from test_lane import host_lane, outputs
from test_pins import rx_unit, uart_wave


# ------------------------------------------------------------------ lanes
def test_l3_registers_read_at_exec_time_latched_at_eval():
    chip, _ = host_lane([
        reflex(op="ADD", dst="r0", a="r0", b=1, state=0, ns=1),
        reflex(op="MOV", dst="O0", a="r0", state=1, ns=2),    # EVAL while r0 is still 0
    ])
    chip.run_for(10)
    assert outputs(chip) == [1]                              # read at EXEC, after the ADD landed
    chip, _ = host_lane([reflex(op="MOV", dst="O0", a="time", state=0, ns=1)])
    chip.run_for(10)
    assert outputs(chip) == [0]                              # the EVAL clock, not EXEC's 1


def test_l8_kt_with_a_non_input_operand_uses_ot():
    chip, _ = host_lane([reflex(op="MOV", dst="O0", a="zero", keep_tag=True, ot="EVENT", state=0, ns=1)])
    chip.host_push(0x55, tag=1)                              # a CTRL head is waiting on I0
    chip.run_for(10)
    assert list(chip.host_out) == [(2, 0)]


def test_l9_pend_set_wins_over_clear_on_the_same_edge():
    chip, lane = host_lane([
        reflex(op="SUB", dst="r0", a="r0", b=1, state=0, ns=1, flag=0),
        reflex(op="ADD", dst="r1", a="r1", b=1, state=1, ns=2, flag=0),
    ])
    chip.run_for(2)          # edge 1: slot 0's EXEC clears PEND[0], slot 1's EVAL sets it
    assert lane.pend[0] == 1
    chip.step()
    assert lane.pend[0] == 0


def test_l10_routine_writes_to_f3_are_ignored():
    body = Routine().clrf(3).cpyf(3).ldi("r1", 7).out("O0", "r1").ret()   # RZ = 0: CPYF 3 would clear RB
    chip, lane = host_lane([reflex(op="CALL", f=0, state=0, ns=1)])
    chip.load_sram(link_routines([body]))
    chip.run_for(80)
    assert outputs(chip) == [7] and lane.rb == 0 and lane.stats["routine_steps"] == 5


def test_r4_reflex_ns_beats_routine_setst_on_the_same_edge():
    chip, lane = host_lane([reflex(op="ADD", dst="r0", a="r0", b=1, state=0, ns=5)])
    lane.exec_latch = {"kind": "routine", "word": Routine().setst(9).assemble()[0], "time": 0}
    lane.rstep_inflight = True
    chip.step()
    assert lane.state == 5


def test_r5_out_with_a_full_output_does_not_hold_back_slots():
    chip = Chip(lanes=1)
    chip.connect("L0.I1", "L0.O0")                           # nobody takes: O0 stays full
    lane = chip.lanes[0]
    lane.load_slot(0, reflex(op="CALL", f=0, state=0, ns=1))
    lane.load_slot(1, reflex(op="ADD", dst="r2", a="r2", b=1, state=1))   # non-urgent
    chip.load_sram(link_routines([Routine().ldi("r1", 1).out("O0", "r1").out("O0", "r1").ret()]))
    chip.run([0])
    chip.run_for(100)
    before = lane.regs[2]
    chip.run_for(40)
    assert lane.regs[2] - before == 40 and lane.rb == 1       # every clock, routine parked


def test_r6_djnz_leaves_rz_unchanged():
    body = (Routine().alu("OR", "r1", "r0", 1)                # d = 1: RZ = 0
            .ldi("r2", 2).label("l").djnz("r2", "l")          # ends at r2 = 0
            .br("yes", "rz").ldi("r3", 5).out("O0", "r3").ret()
            .label("yes").ldi("r3", 9).out("O0", "r3").ret())
    chip, _ = host_lane([reflex(op="CALL", f=0, state=0, ns=1)])
    chip.load_sram(link_routines([body]))
    chip.run_for(120)
    assert outputs(chip) == [5]


# ------------------------------------------------------------ host (H1, H2)
def test_h2_step_runs_one_eval_then_its_exec():
    chip, lane = host_lane([reflex(op="ADD", dst="r0", a="r0", b=1)])
    chip.halt([0])
    chip.run_for(5)
    assert lane.regs[0] == 0
    chip.step_lane(0)
    assert lane.regs[0] == 0                                 # EXEC is in the next clock
    chip.step()
    assert lane.regs[0] == 1
    chip.run_for(5)
    assert lane.regs[0] == 1
    chip.run([0])
    chip.step()                                              # EVAL
    chip.halt([0])
    chip.step()                                              # the selected action still executes
    chip.run_for(5)
    assert lane.regs[0] == 2


def test_h2_halt_stops_routine_fetches():
    body = Routine().ldi("r0", 60).label("l").djnz("r0", "l").ret()
    chip, lane = host_lane([reflex(op="CALL", f=0, state=0, ns=1)])
    chip.load_sram(link_routines([body]))
    chip.run_for(40)
    chip.halt([0])
    chip.run_for(4)
    steps = lane.stats["routine_steps"]
    chip.run_for(50)
    assert lane.stats["routine_steps"] == steps and lane.rb == 1
    # a CALL's entry-table read that is pending at the halt waits too
    chip, lane = host_lane([reflex(op="CALL", f=0, state=0, ns=1)])
    chip.load_sram(link_routines([Routine().ldi("r1", 3).out("O0", "r1").ret()]))
    chip.step()                                              # CALL's EVAL: entry read requested
    chip.halt([0])
    reads = chip.sram.reads
    chip.run_for(20)
    assert chip.sram.reads == reads and lane.mem_req is not None
    chip.run([0])
    chip.run_for(40)
    assert outputs(chip) == [3]


def test_e2_registers_and_k_writable_only_while_halted():
    chip, lane = host_lane([reflex(op="ADD", dst="r0", a="r0", b=1)])
    for write in (lambda: lane.write_reg(0, 5), lambda: lane.write_k(0, 5), lambda: lane.write_state(1)):
        with pytest.raises(RuntimeError):
            write()
    chip.halt([0])
    lane.write_reg(1, 0x1234)
    lane.write_state(3)
    assert lane.regs[1] == 0x1234 and lane.state == 3


# ------------------------------------------------------------------ pins
def test_p19_one_rx_load_per_clock_extra_words_overrun():
    """BUGS #35: a SAMPLE word completing with a LINKED_RX word used to crash the model."""
    chip = rx_unit(rxmode="linked_rx", rx_edge="rise", rx_nbits=1)
    chip.host_push(0x5000, tag=1)                            # SYNC
    for _ in range(30):
        chip.host_push(0x8000 | 1, tag=1)                    # SAMPLE every tick
    for t in range(150):
        chip.ui_in = 0b10 if (t // 2) % 2 else 0             # pin B rises every 4 clocks
        chip.step()
    assert chip.pins[0].flags["OVERRUN"] == 1 and chip.host_out


def test_p15_shift_rx_rearms_after_a_mid_word_deselect():
    """BUGS #36: a deselect in the middle of a word stopped SHIFT_RX for good."""
    chip = rx_unit(rxmode="shift_rx", nbits=10, period=8, idle=1, pin_c=PAD_UI + 2, c_active=0)
    chip.settle_inputs(ui=1)
    half = uart_wave(b"\x55", 8)[:40 + 5 * 8]                # idle, then 5 bits of a frame
    wave = [(b, 0) for b in half] + [(1, 1)] * 50 + [(b, 0) for b in uart_wave(b"\xa5\x3c", 8)]
    for a, c in wave:
        chip.ui_in = a | (c << 2)
        chip.step()
    assert [d for _, d in chip.host_out] == [(0xA5 << 1) | 0x200, (0x3C << 1) | 0x200]


def test_p15_c_oe_gates_the_carrier():
    """BUGS #37: with CARRIER, a deselected unit still drove pin A."""
    chip = Chip(lanes=1)
    chip.settle_inputs(ui=0b100)                             # pin C high: deselected (C_ACTIVE 0)
    chip.pin_config(0, pin_a=PAD_UIO + 0, txmode="level", idle=0, carrier=10,
                    pin_c=PAD_UI + 2, c_active=0, c_oe=True)
    chip.own(PAD_UIO + 0, 0)
    chip.connect("U0.tx", "HOST_IN")
    chip.host_push(0x5000, tag=1)                            # SYNC
    chip.host_push(0x1800 | 5, tag=1)                        # active from +5
    oe = []
    for _ in range(60):
        chip.step()
        oe.append(chip.outputs()[2] & 1)
    assert not any(oe[1:])
    chip.settle_inputs(ui=0)                                 # selected
    oe = []
    for _ in range(30):
        chip.step()
        oe.append(chip.outputs()[2] & 1)
    assert any(oe)


@pytest.mark.parametrize("partial, emitted", [([0], [(0, 0b10)]), ([], [])])
def test_p18_restart_clock_sample_is_kept_only_if_it_completes_a_word(partial, emitted):
    chip = rx_unit(rxmode="linked_rx", rx_edge="rise", rx_nbits=2)
    chip.settle_inputs(ui=0)
    chip.run_for(3)
    u = chip.pins[0]
    u._rx_bits = list(partial)
    u._schedule(chip.cycle, "rxlen", 3)                      # SETN rx due in this clock
    chip.settle_inputs(ui=0b11)                              # pin B rises in this clock, A = 1
    chip.step()
    chip.run_for(5)
    assert list(chip.host_out) == emitted and u._rx_bits == [] and u._rx_len == 3


# ------------------------------------------------------- BITSYNC (P20-P29)
def bitsync_unit(**cfg):
    chip = Chip(lanes=1)
    chip.pin_config(0, pin_a=PAD_UIO + 0, pin_s=PAD_UI + 0, txmode="bitsync", rxmode="bitsync",
                    period=20, idle=1, idle_bits=8, rx_nbits=8, **cfg)
    chip.connect("U0.tx", "HOST_IN")
    chip.connect("HOST_OUT", "U0.rx")
    return chip


def test_bitsync_setn_rx_out_of_range_means_16():
    """BUGS #38: SETN rx with n = 17..31 gave words longer than 16 bits."""
    chip = bitsync_unit()
    chip.host_push(0x6020 | 20, tag=1)
    chip.run_for(5)
    assert chip.pins[0].bs.rx_len == 16


@pytest.mark.parametrize("delim", ["flag", "se0"])
def test_bitsync_frame_end_event_carries_own_bit(delim):
    """BUGS #39: frames ended by a flag or by SE0 lacked EVENT data[14] = own frame (§14 P24)."""
    chip = bitsync_unit(delim=delim, stuff_n=5, stuff_lvl=1)
    bs = chip.pins[0].bs
    bs.in_frame = bs.rx_on = bs.own = True
    bs.hunting, bs.bits, bs.frame_bits = False, [1, 0, 1], 3
    if delim == "flag":
        bs._flag_close()
    else:
        bs.sense_b = 0
        bs._sample_bit(0)
    assert list(bs.out) == [(2, 0b101 | 1 << 14)]


# ------------------------------------------------- pin-unit RTL gaps (D-041)
def _unit(**cfg):
    chip = Chip(lanes=1)
    chip.pin_config(0, **cfg)
    if cfg.get("pin_a") is not None and cfg["pin_a"] >= PAD_UO:
        chip.own(cfg["pin_a"], 0)
    chip.connect("U0.tx", "HOST_IN")
    chip.connect("HOST_OUT", "U0.rx")
    return chip, chip.pins[0]


def _runs(levels):
    return [v for i, v in enumerate(levels) if i == 0 or v != levels[i - 1]]


def test_p31_pin_n_complements_pin_a_before_open_drain():
    chip, _ = _unit(pin_a=PAD_UIO + 0, pin_n=PAD_UIO + 1, txmode="level", od=True, idle=1)
    chip.own(PAD_UIO + 1, 0)
    chip.host_push(0x1000, tag=1)                            # LEVEL 0: A pulls low
    chip.run_for(10)
    _, uio, oe = chip.outputs()
    assert (uio & 1, oe & 1) == (0, 1) and ((uio >> 1) & 1, (oe >> 1) & 1) == (1, 1)
    chip.host_push(0x1800, tag=1)                            # LEVEL 1: A released, N drives low
    chip.run_for(10)
    _, uio, oe = chip.outputs()
    assert oe & 1 == 0 and ((uio >> 1) & 1, (oe >> 1) & 1) == (0, 1)


def test_p32_a_gap_that_runs_too_far_ahead_waits():
    chip, u = _unit(pin_a=PAD_UO + 0, txmode="level", idle=0)
    chip.host_push(0x5000, tag=1)                            # SYNC
    for _ in range(9):
        chip.host_push(0x4000 | 4095, tag=1)                 # GAP 4095
    chip.run_for(100)
    assert u.stats["tx_tokens"] == 9                         # 8 GAPs = 32 760 ticks ahead; the 9th waits
    chip.run_for(4200)
    assert u.stats["tx_tokens"] == 10


def test_p32_a_cursor_far_in_the_past_moves_up():
    chip, u = _unit(pin_a=PAD_UO + 0, txmode="level", idle=0)
    chip.host_push(0x5000, tag=1)                            # SYNC, then 40 000 clocks pass
    chip.run_for(40000)
    for _ in range(9):
        chip.host_push(0x4000 | 4095, tag=1)                 # from now - 32 767: lands ~4 088 ahead
    chip.host_push(0x1800, tag=1)                            # LEVEL 1 at the cursor
    chip.run_for(200)
    assert chip.outputs()[0] & 1 == 0                        # unbounded, it would be past: high at once
    chip.run_for(4200)
    assert chip.outputs()[0] & 1 == 1 and u.flags["LATE"] == 0


def test_p33_clkgen_odd_period_does_not_drift():
    chip, u = _unit(pin_a=PAD_UO + 0, txmode="clkgen", period=10 + 255 / 256, idle=0)
    chip.host_push(0x3000 | 255, tag=1)                      # CLK 255
    while u.clk is None:
        chip.step()
    start9 = u.clk["t9"] - u.cfg.period_q8
    while u.clk is not None:
        chip.step()
    assert 2 * u.cursor_q8 - start9 == 255 * 2 * u.cfg.period_q8     # exactly 255 periods


def test_p34_data_at_clkgen_is_ignored_and_short_periods_rejected():
    chip, u = _unit(pin_a=PAD_UO + 0, txmode="clkgen", period=4, idle=0)
    chip.host_push(0xFFFF)
    seen = set()
    for _ in range(40):
        chip.step()
        seen.add(chip.outputs()[0] & 1)
    assert seen == {0} and u.stats["bad_tokens"] == 1
    with pytest.raises(ValueError, match="period >= 2"):
        chip.pin_config(0, pin_a=PAD_UO + 0, txmode="clkgen", period=1.5)


def test_p34_burst_count_is_9_bits():
    chip, u = _unit(pin_a=PAD_UO + 0, txmode="clkgen", period=2, idle=0)
    for n in (255, 255, 5):
        chip.host_push(0x3000 | n, tag=1)
    most = 0
    for _ in range(3000):
        chip.step()
        if u.clk:
            most = max(most, u.clk["n"])
    assert most <= 511 and u.stats["tx_tokens"] == 3


def test_p36_linked_bits_wait_while_deselected():
    chip, _ = _unit(pin_a=PAD_UO + 0, pin_b=PAD_UI + 1, pin_c=PAD_UI + 2, c_active=0, txmode="shift",
                    tx_edge="rise", tx_preload=True, nbits=4, order="lsb", idle=0)
    chip.settle_inputs(ui=0b100)                             # deselected, B low
    chip.host_push(0b1001)
    chip.run_for(6)

    def edge(sel):
        base = 0 if sel else 0b100
        chip.ui_in = base | 0b10
        chip.run_for(4)
        chip.ui_in = base
        chip.run_for(4)
        return chip.outputs()[0] & 1

    assert chip.outputs()[0] & 1 == 1                        # bit 0 preloaded while deselected (P15)
    assert [edge(False) for _ in range(3)] == [1, 1, 1]      # another target's clock: no shift
    assert [edge(True) for _ in range(4)] == [0, 0, 1, 0]    # selected: bits 1-3, then IDLE


def test_p36_the_preload_clock_edge_is_used_by_the_preload():
    for lag in range(10):
        chip, _ = _unit(pin_a=PAD_UO + 0, pin_b=PAD_UI + 1, txmode="shift", tx_edge="rise",
                        tx_preload=True, nbits=3, order="lsb", idle=0)
        trace = []
        for t in range(60):
            if t == 5:
                chip.host_push(0b101)                        # bits 1, 0, 1
            chip.ui_in = 0b10 if t >= lag and (t - lag) % 8 < 4 else 0
            chip.step()
            trace.append(chip.outputs()[0] & 1)
        assert _runs(trace)[:4] == [0, 1, 0, 1], lag         # bit 1 never goes out before bit 0


def test_p37_setn_rx_rearms_shift_rx():
    chip, _ = _unit(pin_a=PAD_UI + 0, rxmode="shift_rx", nbits=10, period=8, idle=1, autorearm=False)
    chip.settle_inputs(ui=1)

    def send(byte):
        it = iter(uart_wave(bytes([byte]), 8))
        chip.run_for(len(uart_wave(bytes([byte]), 8)), env=lambda c: setattr(c, "ui_in", next(it)))

    send(0x41)
    send(0x42)                                               # stopped: not received
    chip.host_push(0x6020 | 10, tag=1)                       # SETN rx 10: re-arms
    chip.run_for(5)
    send(0x43)
    assert [d >> 1 & 0xFF for _, d in chip.host_out] == [0x41, 0x43]


def test_p38_a_sample_in_an_event_clock_still_counts():
    """BUGS #41: an edge event in a SHIFT_RX sample clock skipped the sample, and SHIFT_RX
    (which matches each sample time exactly) then never finished its word."""
    for d in range(-4, 5):                                   # move one mid-frame edge across the samples
        chip, _ = _unit(pin_a=PAD_UI + 0, rxmode="shift_rx", nbits=10, period=8, idle=1,
                        sampleofs=0.5, ev_edge="both", autorearm=False)
        chip.settle_inputs(ui=1)
        wave = [1] * 40 + [0] * 8 + [1] * (24 + d) + [0] * (48 - d) + [1] * 60
        it = iter(wave)
        chip.run_for(len(wave), env=lambda c: setattr(c, "ui_in", next(it)))
        assert len([1 for tag, _ in chip.host_out if tag == 0]) == 1, d


def test_p38_one_framing_bit_per_clock():
    overran = []
    for off in range(4):
        chip, u = _unit(pin_a=PAD_UI + 0, pin_b=PAD_UI + 1, rxmode="linked_rx", rx_edge="rise", rx_nbits=16)
        per_clock = {}
        orig = u._sample

        def counting(bit, orig=orig, chip=chip, per_clock=per_clock):
            per_clock[chip.cycle] = per_clock.get(chip.cycle, 0) + 1
            orig(bit)
        u._sample = counting
        chip.host_push(0x5000, tag=1)                        # SYNC
        chip.host_push(0x8000 | (10 + off), tag=1)           # SAMPLE
        for t in range(40):
            chip.ui_in = 0b10 if t % 4 < 2 else 0            # B rises every 4 clocks
            chip.step()
        assert max(per_clock.values()) == 1, off
        overran.append(u.flags["OVERRUN"])
    assert any(overran)                                      # the SAMPLE on an edge clock was dropped


def test_p40_a_level_ends_taint():
    chip, u = _unit(pin_a=PAD_UO + 0, txmode="level", idle=0)
    u.driving = True                                         # as if a shifted bit were on the pad
    chip.host_push(0x1800, tag=1)                            # LEVEL 1
    chip.run_for(8)
    assert chip.outputs()[0] & 1 == 1 and not u.driving


def test_p41_p42_out_of_range_lengths_and_pads_are_rejected():
    for bad in (dict(rx_nbits=17), dict(rx_nbits2=20), dict(pin_a=24), dict(pin_b=30)):
        with pytest.raises(ValueError):
            Chip(lanes=1).pin_config(0, **bad)
    words = pinregs.encode(PinConfig())
    bit = S.PIN_CFG_FIELDS["pin_a"][0]
    words[bit // 16] = (words[bit // 16] & ~(0x1F << bit % 16)) | (26 << bit % 16)
    assert pinregs.decode(words).pin_a is None               # codes 24-30 act as 31


def test_p42_an_unattached_pin_a_samples_idle():
    chip, _ = _unit(rx_nbits=1, idle=1)
    chip.host_push(0x8000, tag=1)                            # SAMPLE, no pin A
    chip.run_for(10)
    assert list(chip.host_out) == [(0, 1)]


def test_p43_unnamed_enum_codes_act_as_code_0():
    words = pinregs.encode(PinConfig())
    for name, code in (("ev_qual", 1), ("tx_edge", 3)):
        bit, width, _ = S.PIN_CFG_FIELDS[name]
        mask = ((1 << width) - 1) << bit % 16
        words[bit // 16] = (words[bit // 16] & ~mask) | (code << bit % 16)
    back = pinregs.decode(words)
    assert back.ev_qual is None and back.tx_edge is None


@pytest.mark.parametrize("pending, winner", [("return", 0), ("bit", 1)])
def test_p44_same_edge_order_in_linked_mode(pending, winner):
    chip, u = _unit(pin_a=PAD_UO + 0, pin_b=PAD_UI + 1, txmode="shift", tx_edge="rise", idle=1)
    chip.settle_inputs(ui=0b10)                              # B synchronised high this clock
    u._prev_b_tx = 0                                         # so the clock sees a rising edge
    if pending == "return":
        u.linked_end = True                                  # return to IDLE (1) is due on the edge
        u.actions = [(chip.cycle, "level", 0)]               # a LEVEL 0 lands on the same edge
    else:
        u.linked_bits = [1]
        u.actions = [(chip.cycle, "level", 0)]
    chip.step()
    assert u.level == winner                                 # LEVEL beats the return; a bit beats LEVEL

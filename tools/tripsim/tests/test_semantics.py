"""ARCHITECTURE.md §14 rules pinned by the second-person review (DECISIONS D-035).

One test per rule that no other test pins down, plus regressions for BUGS #35-#39.
A few tests set lane or pin-unit state directly, to hit an exact same-clock case.
"""

import pytest

from tripsim import PAD_UI, PAD_UIO, Chip
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

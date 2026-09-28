"""ARCHITECTURE.md §14 rules pinned by the second-person review (DECISIONS D-035).

One test per rule that no other test pins down, plus regressions for BUGS #35-#39.
A few tests set lane or pin-unit state directly, to hit an exact same-clock case.
"""

import pytest

import tripwire_spec as S
from tripsim import PAD_UI, PAD_UIO, PAD_UO, Chip, pinregs
from tripsim.pinunit import PinConfig
from tripsim.isa import TAG_DATA
from tripsim.asm import Routine, link_routines, reflex

from test_lane import host_lane, outputs
from test_pins import rx_unit, uart_wave


def test_d042_unit_flags_are_readable_and_write_one_to_clear():
    chip = Chip()
    chip.pins[0].flags.update(OVERRUN=1, LATE=1)
    base = S.HOST_MAP["unit_flags"][0]
    assert chip.host_read(base) == 3
    chip.host_write(base, 1)
    assert chip.host_read(base) == 2
    chip.host_write(base, 0)
    assert chip.host_read(base) == 2


def test_d044_host_port_map_f5_and_dropped_clear():
    chip = Chip(lanes=1, pin_units=1)
    ports = S.HOST_MAP["ports"][0]
    dropped = S.HOST_MAP["dropped"][0]
    consumer = chip.fabric.ports["L0.I0"]
    p = chip.fabric.producers["HOST_IN"]
    p.valid, p.seq, p.tag, p.data = 1, 1, 0, 0x55
    # HOST_IN's index in the generated legal source list is the address encoding.
    sel = S.LEGAL_SOURCES["L0.I0"].index("HOST_IN")
    chip.host_write(ports, 1 | (sel << 2) | (0xF << 6))
    assert consumer.last_seq == 1 and not consumer.avail()  # F5 suppresses the stale head
    p.load(2, 0x66)
    chip.step()                                               # source load at this same edge
    assert consumer.avail() and consumer.head() == (2, 0x66)
    consumer.dropped = 9
    assert chip.host_read(dropped) == 9
    chip.host_write(dropped, 0xFFFF)
    assert chip.host_read(dropped) == 0


def test_d044_out_of_range_sel_disables_source_selection():
    chip = Chip(lanes=1, pin_units=1)
    addr = S.HOST_MAP["ports"][0]
    chip.host_write(addr, 1 | (15 << 2) | (15 << 6))
    c = chip.fabric.ports["L0.I0"]
    assert c.src is None and not c.avail()
    assert (chip.host_read(addr) >> 2) & 15 == 15


def test_d044_port_configuration_write_wins_over_same_clock_take():
    chip = Chip(lanes=1, pin_units=1)
    addr = S.HOST_MAP["ports"][0]
    port = chip.fabric.ports["L0.I0"]
    old_src = chip.fabric.producers["HOST_IN"]
    new_src = chip.fabric.producers["U0.rx"]
    new_src.valid, new_src.seq, new_src.tag, new_src.data = 1, 1, 0, 0x5A
    old_sel = S.LEGAL_SOURCES[port.name].index("HOST_IN")
    chip.host_write(addr, 1 | (old_sel << 2) | (0xF << 6))
    old_src.valid, old_src.seq, old_src.tag, old_src.data = 1, 1, 0, 0xA5
    assert port.avail()
    port.take()                                               # same-clock lane take
    new_sel = S.LEGAL_SOURCES[port.name].index("U0.rx")
    assert chip.host_write(addr, 1 | (new_sel << 2) | (0xF << 6))  # host config wins
    chip.fabric.commit()
    assert port.src is new_src and port.last_seq == new_src.seq
    assert port.takes == 0 and not port._take and not port.avail()


def test_d046_host_map_tagged_host_in_and_lane_debug_reads():
    chip = Chip(lanes=1, pin_units=1)
    hin = S.HOST_MAP["host_in"][0]
    status = S.HOST_MAP["host_status"][0]
    assert chip.host_read(status) & (1 << 14)
    assert chip.host_write(hin + 3, 0x1234)
    assert not chip.host_read(status) & (1 << 14)
    assert not chip.host_write(hin + 2, 0x5678)
    chip.step()
    p = chip.fabric.producers["HOST_IN"]
    assert (p.tag, p.data) == (3, 0x1234)
    lane = chip.lanes[0]
    lane.regs[:] = [0x10, 0x11, 0x12, 0x13]
    base = S.HOST_MAP["lanes"][0]
    assert [chip.host_read(base + i) for i in range(4)] == lane.regs
    assert chip.host_read(base + 4) == lane.state
    lane.rpc, lane.rz = 0x123, 1
    assert chip.host_read(base + 6) == 0x123
    assert chip.host_read(base + 7) == (1 << 14)


def test_d046_slot_k_and_owner_host_addresses():
    chip = Chip(lanes=1, pin_units=1)
    lane = chip.lanes[0]
    slot_base = S.HOST_MAP["slots"][0]
    lane_word = (S.SLOT_HOST_WORDS - 1)  # write the top half of one reflex slot
    assert chip.host_write(slot_base + (lane_word), 0x1234)
    assert lane.slots[0].V == 0  # partial slot remains invalid until its V word is written
    assert chip.host_write(slot_base + (12 << 4), 0x5678)  # K0, slot 12, word 0
    assert lane.k[0] == 0x5678
    owner_base = S.HOST_MAP["owners"][0]
    assert chip.host_write(owner_base, 0)
    assert chip.host_read(owner_base) == 0
    assert not chip.host_write(owner_base + (S.HOST_PADS[3] - 8), 0)


def test_d041_a_configuration_write_restarts_unit_and_resets_event_epoch():
    chip = Chip(lanes=1, pin_units=1)
    cfg = dict(pin_a=PAD_UI, rxmode="linked_rx", ev_edge="both", presc=4)
    chip.pin_config(0, **cfg)
    unit = chip.pins[0]
    unit.flags.update(LATE=1, OVERRUN=1)
    unit.cursor_q8, unit.tx_nbits, unit._car_n = 0x1234, 2, 9
    chip.run_for(20)
    configured_at = chip.cycle
    chip.pin_config(0, **cfg)
    assert unit.t_cfg == configured_at
    assert unit.flags == {"LATE": 0, "OVERRUN": 0}
    assert unit.cursor_q8 == 0 and unit.tx_nbits == unit.cfg.nbits and unit._car_n == 0
    unit._prev_a = 0
    unit._emit = lambda tag, data: setattr(unit, "_test_event", (tag, data))
    unit.compute_rx(configured_at + 7, 1, 0)
    assert unit._test_event[1] & 0x7FFF == 1            # (cycle - t_cfg) // PRESC


def test_d041_b_units_wait_for_first_run_or_step():
    chip = Chip(lanes=1, pin_units=1)
    chip.pin_config(0, pin_a=PAD_UO, txmode="level", idle=0)
    chip.connect("U0.tx", "HOST_IN")
    chip.host_push(0x5000, tag=1)                         # SYNC
    chip.host_push(0x1800 | 3, tag=1)                     # LEVEL 1
    chip.run_for(20)
    assert not chip.live and chip.pins[0].stats["tx_tokens"] == 0
    assert chip.fabric.producers["U0.rx"].loads == 0
    assert chip.host_read(S.HOST_MAP["run"][0]) & (1 << S.HOST_RUN_LIVE_BIT) == 0
    chip.run([0])                                         # empty lane RUN is sufficient
    chip.run_for(20)
    assert chip.live and chip.pins[0].stats["tx_tokens"] > 0
    assert chip.host_read(S.HOST_MAP["run"][0]) & (1 << S.HOST_RUN_LIVE_BIT)
    stepped = Chip(lanes=1, pin_units=1)
    assert stepped.host_write(S.HOST_MAP["step"][0], 1)
    assert stepped.live and stepped.host_read(S.HOST_MAP["run"][0]) & (1 << S.HOST_RUN_LIVE_BIT)


def test_d041_a_host_pin_cfg_word_write_restarts_and_clears_flags():
    chip = Chip(lanes=1, pin_units=1)
    unit = chip.pins[0]
    unit.flags.update(LATE=1, OVERRUN=1)
    unit.cursor_q8 = 0x4321
    base = S.HOST_MAP["pin_cfg"][0]
    assert chip.host_write(base, 1 << 7)                    # word 0: IDLE=1
    assert unit.cfg.idle == 1 and unit.cursor_q8 == 0
    assert unit.flags == {"LATE": 0, "OVERRUN": 0}
    assert unit.t_cfg == chip.cycle


def test_d045_lane_fetch_timing_matches_r1_and_r2_reading():
    body = Routine().ldi("r0", 7).out("O0", "r0").ret()
    chip, lane = host_lane([reflex(op="CALL", f=0, state=0, ns=1)])
    chip.load_sram(link_routines([body]))
    lane.running = True
    chip.run_for(4)                                           # reach L0's SRAM rotation slot
    assert lane.rb and lane.mem_req is not None               # CALL requested entry fetch
    observed = []
    chip.observers.append(lambda c: observed.append((c.cycle, lane.stats["routine_steps"], lane.regs[0])))
    chip.run_for(12)                                          # entry read, routine-word fetch/EVAL/EXEC
    assert lane.regs[0] == 7
    first_eval = next(c for c, n, _ in observed if n)
    first_exec = next(c for c, _, r in observed if r == 7)
    assert first_exec == first_eval + 1                      # k+1 EVAL, k+2 EXEC


def test_d045_step_and_host_lane_writes_are_ignored_while_running():
    chip, lane = host_lane([reflex(op="ADD", dst="r0", a="r0", b=1)])
    lane.running = True
    before = lane.regs[0]
    assert not chip.host_write(S.HOST_MAP["lanes"][0], 0x1234)
    assert lane.regs[0] == before
    assert chip.host_write(S.HOST_MAP["step"][0], 1)
    assert not lane.stepping


def test_d045_fetch_waits_for_exec_and_rir_to_clear_and_advances_rpc_at_fetch():
    chip = Chip(lanes=1, pin_units=1)
    lane = chip.lanes[0]
    lane.rb = 1
    chip.load_sram(link_routines([Routine().ldi("r0", 7)]))

    lane.rstep_inflight = True                              # routine instruction is in EXEC
    lane.mem_access(chip.sram)
    assert chip.sram.reads == 0 and lane.rpc == 0

    lane.rstep_inflight = False
    lane.rir = ("instr", chip.sram.mem[0])                  # decoded step waits for EVAL
    lane.mem_access(chip.sram)
    assert chip.sram.reads == 0 and lane.rpc == 0

    lane.rir = None
    lane.mem_access(chip.sram)                               # a fetch itself advances RPC
    fetched = lane._m["rir"]
    lane.commit()
    assert chip.sram.reads == 1 and lane.rpc == 1
    assert lane.rir == fetched == ("instr", chip.sram.mem[0])


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
    chip.run([0])
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


def test_p30_fractional_carrier_toggles_at_floor_half_period_boundaries():
    chip = Chip(lanes=1, pin_units=1)
    chip.pin_config(0, txmode="level", idle=0, carrier=5.5)
    unit = chip.pins[0]
    unit.level = 1
    # floor(k * 5.5 / 2) gives toggle edges 2, 5, 8, 11.
    levels = []
    for elapsed in range(12):
        unit._car_n = elapsed
        levels.append(unit.pad_drive()[0])
    assert levels == [1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1]


def test_p17_zero_tick_pulse_phase_is_clamped_to_one_clock():
    chip = Chip(lanes=1, pin_units=1)
    unit = chip.pins[0]
    unit.configure(validate=False, txmode="pulse", idle=0, nbits=1,
                    sym0_first=0, sym0_t1=0, sym0_t2=0)
    unit._accept(0, TAG_DATA, 0)                            # one DATA bit, earliest edge 1
    assert unit.actions == [(1, "sbit", 0), (2, "sbit", 1), (3, "send", 0)]
    unit.compute_tx(1)
    unit.commit()
    assert unit.level == 0                                  # first phase begins at its earliest edge


def test_p30_carrier_below_two_clocks_is_off():
    chip = Chip(lanes=1, pin_units=1)
    chip.pin_config(0, txmode="level", idle=0, carrier=1.5)
    unit = chip.pins[0]
    unit.level = 1
    levels = []
    for elapsed in range(6):
        unit._car_n = elapsed
        levels.append(unit.pad_drive()[0])
    assert levels == [1] * 6


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
    config = dict(pin_a=PAD_UIO + 0, pin_s=PAD_UI + 0, txmode="bitsync", rxmode="bitsync",
                  period=20, idle=1, idle_bits=8, rx_nbits=8)
    config.update(cfg)
    chip.pin_config(0, **config)
    chip.connect("U0.tx", "HOST_IN")
    chip.connect("HOST_OUT", "U0.rx")
    chip.run([0])                                           # D-041 B: first RUN makes units live
    return chip


def test_bitsync_setn_rx_out_of_range_means_16():
    """BUGS #38: SETN rx with n = 17..31 gave words longer than 16 bits."""
    chip = bitsync_unit()
    chip.host_push(0x6020 | 20, tag=1)
    chip.run_for(5)
    assert chip.pins[0].bs.rx_len == 16


def test_p20_idle_making_sample_closes_frame_before_word_framing():
    chip = bitsync_unit(idle_bits=2, rx_nbits=8)
    bs = chip.pins[0].bs
    bs.in_frame = bs.rx_on = True
    bs.idle_cnt = 1
    bs.frame_bits = 0
    bs.bits = []
    bs._sample_bit(1)                                       # reaches IDLE_BITS and ends frame
    assert bs.frame_bits == 0 and bs.bits == []
    assert bs.bitno == 1
    assert not bs.in_frame                                  # D-052 P-G29


def test_p8_event_generator_runs_in_bitsync_and_wins_same_clock_load():
    chip = bitsync_unit(ev_edge="rise")
    unit = chip.pins[0]
    unit._prev_a = 0
    unit.bs.out.append((S.TAGS["DATA"], 0x55))              # older BITSYNC result waits behind P8
    unit.compute_rx(chip.cycle, 1, 1)                        # pin A rises
    assert unit.rx_prod._load == (S.TAGS["EVENT"], 0x8000)
    assert list(unit.bs.out) == [(S.TAGS["DATA"], 0x55)]


def test_p23_stuff_error_reports_one_based_line_bit_count():
    chip = bitsync_unit(stuff_n=1, stuff_lvl=0)
    bs = chip.pins[0].bs
    bs.in_frame = bs.rx_on = bs.rx_stuff = True
    bs.bitno = 0
    bs.run_lvl, bs.run_n = 0, 1                              # next zero violates stuffing
    bs._sample_bit(0)
    assert list(bs.out) == [(S.TAGS["ERR"], 0x1001)]        # D-053 P-G27 calls this an index


def test_p24_frame_limit_emits_verdict_for_current_word_only():
    chip = bitsync_unit(rx_nbits=8)
    bs = chip.pins[0].bs
    bs.in_frame = bs.rx_on = True
    bs.frame_n = 1
    bs.rx_stuff = False
    bs._sample_bit(1)
    assert list(bs.out) == [(S.TAGS["EVENT"], 1)]          # D-053 P-G30: no DATA on verdict clock


def test_p25_wait_sp_releases_and_accepts_tx_token_on_sample_clock():
    chip = bitsync_unit()
    unit = chip.pins[0]
    bs = unit.bs
    bs.wait_sp = True
    p = chip.fabric.producers["HOST_IN"]
    p.valid, p.seq, p.tag, p.data = 1, 1, TAG_DATA, 0x01
    bs.step(10, 1, 1)                                       # sample point at half of P=20
    bs.accept(10, unit.tx_port, {})
    assert not bs.wait_sp and unit.tx_port._take
    assert list(bs.q)[0] == ("b", 1, True)                  # D-054 P-G31


def test_p25_own_frame_opens_at_next_bit_boundary_with_started_event():
    chip = bitsync_unit()
    bs = chip.pins[0].bs
    bs.newframe, bs.idle_cnt, bs.sampled = True, chip.pins[0].cfg.idle_bits, True
    bs.t = 0
    bs.q.append(("b", 0, True))
    bs.step(19, 1, 1)                                        # one clock before t + P
    assert not bs.in_frame and not bs.out
    bs.step(20, 1, 1)                                        # exact next bit boundary
    assert bs.in_frame and bs.own and bs.t == 20 * 256
    assert chip.pins[0].rx_prod._load == (S.TAGS["EVENT"], 0x9001)  # D-054 P-G32


def test_p23_due_stuff_bit_waits_for_following_data():
    chip = bitsync_unit(stuff_n=2)
    bs = chip.pins[0].bs
    bs.tx_stuff, bs.tx_run_lvl, bs.tx_run_n = True, 0, 2
    bs._tx_bit_start(0)
    assert bs.tx_bit is None and bs.u._tx_apply[-1] == (0, "level", bs.rec)
    # D-061: without following queued data or CRC, P25 releases the line.


def test_p25_tx_stuffing_run_restarts_at_frame_start():
    bs = bitsync_unit().pins[0].bs
    bs.tx_run_lvl, bs.tx_run_n = 0, 4
    bs._start_frame(12 * 256)
    assert bs.tx_run_lvl is None and bs.tx_run_n == 0          # D-054 P-G34


def test_p25_released_line_is_not_own_edge_and_allows_idle_close():
    chip = bitsync_unit(idle_bits=2)
    bs = chip.pins[0].bs
    bs.prev, bs.idle_cnt, bs.tx_line, bs.tx_bit = bs.rec, 2, None, None
    bs.step(1, 0, 1)                                          # external dominant edge
    assert bs.in_frame and not bs.own                       # release did not claim this edge

    bs2 = bitsync_unit(idle_bits=2).pins[0].bs
    bs2.in_frame = bs2.rx_on = True
    bs2.idle_cnt = 1
    bs2.tx_line = None                                      # line released by our unit
    bs2._sample_bit(bs2.rec)
    assert not bs2.in_frame                                  # idle can end the observed frame


def test_p28_response_jam_taken_in_own_frame_is_discarded():
    chip = bitsync_unit()
    unit = chip.pins[0]
    bs = unit.bs
    bs.in_frame = bs.own = True
    p = chip.fabric.producers["HOST_IN"]
    jam_word = (S.PIN_CMD["JAM"] << 12) | (1 << 5)         # response JAM, level 1, one bit
    p.valid, p.seq, p.tag, p.data = 1, 1, S.TAGS["CTRL"], jam_word
    cmds = {n: S.PIN_CMD[n] for n in ("FRAME", "JAM", "SETN")}
    bs.accept(0, unit.tx_port, cmds)
    assert bs.jam is None                                   # P-G36 judges eligibility at take
    bs.in_frame = bs.own = False                            # frame ends before its next bit
    bs._tx_bit_start(1)
    assert bs.tx_bit is None                                # the refused response cannot fire later


def test_p28_flag_abort_error_carries_current_line_bit_count():
    bs = bitsync_unit(delim="flag", stuff_n=5, stuff_lvl=1).pins[0].bs
    bs.in_frame = bs.rx_on = True
    bs.after6, bs.hunting = True, False
    bs.frame_bits, bs.bits, bs.bitno = 1, [0], 8
    bs._sample_bit(1)                                       # seventh one aborts at count 9
    assert list(bs.out) == [(S.TAGS["ERR"], 0x2009)]        # D-055 P-G37


def test_p28_jam_bit_zero_without_armed_bit_is_ignored():
    chip = bitsync_unit()
    unit = chip.pins[0]
    bs = unit.bs
    p = chip.fabric.producers["HOST_IN"]
    p.valid, p.seq, p.tag = 1, 1, S.TAGS["CTRL"]
    p.data = S.PIN_CMD["JAM"] << 12 | 1                    # [0] set, [4] clear
    cmds = {n: S.PIN_CMD[n] for n in ("FRAME", "JAM", "SETN")}
    bs.accept(0, unit.tx_port, cmds)
    assert bs.jam is None


def test_p28_jam_bits_do_not_enable_readback():
    bs = bitsync_unit().pins[0].bs
    bs.rb = 2
    bs.jam = [1, 1, 0, False]
    bs._tx_bit_start(0)
    assert bs.tx_bit == 1 and bs.tx_rb == 0                 # D-055 P-G39


def test_p23_foreign_frame_stuff_error_preserves_queued_tx():
    bs = bitsync_unit(stuff_n=1, stuff_lvl=0).pins[0].bs
    bs.in_frame, bs.rx_on, bs.rx_stuff, bs.own = True, True, True, False
    bs.run_lvl, bs.run_n = 0, 1
    bs.q.append(("b", 1, True))
    bs._sample_bit(0)
    assert list(bs.q) == [("b", 1, True)] and not bs.own


def test_p26_status_event_wait_register_holds_one_pending_event():
    bs = bitsync_unit().pins[0].bs
    bs._emit(S.TAGS["EVENT"], 0xA001)
    bs._emit(S.TAGS["EVENT"], 0xA002)
    assert list(bs.out) == [(S.TAGS["EVENT"], 0xA001)]
    bs._emit(S.TAGS["EVENT"], 0xA003)
    assert list(bs.out) == [(S.TAGS["EVENT"], 0xA001)]
    assert bs.u.flags["OVERRUN"]


def test_p26_each_tx_bit_carries_the_readback_mode_at_bit_start():
    bs = bitsync_unit().pins[0].bs
    bs.q.extend([("line", 2), ("b", 0, True), ("line", 0), ("b", 1, True)])
    bs._tx_bit_start(0)
    assert bs.tx_rb == 2
    bs._sample_bit(1)                                       # mode 2 reports even without error
    bs._tx_bit_start(1)
    assert bs.tx_rb == 0
    bs._sample_bit(0)
    assert list(bs.out) == [(S.TAGS["EVENT"], 0xE000)]     # D-055 P-G42


def test_p28_jam_delay_counts_to_bit_start_then_disarms_when_fired():
    bs = bitsync_unit().pins[0].bs
    bs.jam = [1, 1, 1, False]                               # one more sample point
    bs._sample(1)
    assert bs.jam[2] == 0
    bs._tx_bit_start(1)
    assert bs.tx_bit == 1 and bs.jam is None                # D-055 P-G43


def test_p23_stuff_run_counts_started_bits_not_queued_bits():
    bs = bitsync_unit(delim="flag", stuff_n=5).pins[0].bs
    bs.q.extend([("b", 1, True), ("b", 1, True)])
    assert bs.tx_run_n == 0
    bs._tx_bit_start(0)
    assert bs.tx_bit == 1 and bs.tx_run_n == 1               # D-055 P-G44


def test_p28_listen_only_clears_tx_queue_and_both_jam_states():
    chip = bitsync_unit()
    unit = chip.pins[0]
    bs = unit.bs
    bs.q.append(("b", 1, True))
    bs.jam, bs.jam_armed = [0, 2, 0, False], (1, 3)
    p = chip.fabric.producers["HOST_IN"]
    p.valid, p.seq, p.tag = 1, 1, S.TAGS["CTRL"]
    p.data = (S.PIN_CMD["JAM"] << 12) | 2                 # JAM [1]: listen-only
    cmds = {n: S.PIN_CMD[n] for n in ("FRAME", "JAM", "SETN")}
    bs.accept(0, unit.tx_port, cmds)
    assert bs.tx_off and not bs.q and bs.jam is None and bs.jam_armed is None  # P-G45


def test_p26_readback_abort_event_carries_level_and_line_bit_index():
    bs = bitsync_unit().pins[0].bs
    bs.tx_bit, bs.tx_rb, bs.bitno = 0, 1, 4
    bs._sample_bit(1)
    assert list(bs.out) == [(S.TAGS["EVENT"], 0xC008)]     # D-055 P-G46
    assert not bs.own


def test_p29_se0_ends_frame_only_when_both_sampled_lines_are_low():
    bs = bitsync_unit(delim="se0", stuff_n=0).pins[0].bs
    bs.in_frame = bs.rx_on = bs.own = True
    bs.bits, bs.sense_b = [1, 0, 1], 1
    bs._sample_bit(0)
    assert bs.in_frame and not bs.out
    bs.sense_b = 0
    bs._sample_bit(0)
    assert not bs.in_frame and list(bs.out) == [(S.TAGS["EVENT"], 0b0101 | (1 << 14))]
    # D-055 P-G47: SE0 ends after the second line is also low; its sample is not frame data.


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
    chip.run([0])
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

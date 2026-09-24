"""Lane scheduling, pipeline timing and routines (ISA.md §4-§5, ARCHITECTURE.md §14)."""

from tripsim import Chip
from tripsim.asm import Routine, link_routines, reflex


def host_lane(slots, regs=None, k=None, lanes=1):
    """Lane 0 with I0 <- HOST_IN and O0 -> HOST_OUT."""
    chip = Chip(lanes=lanes)
    chip.connect("L0.I0", "HOST_IN")
    chip.connect("HOST_OUT", "L0.O0")
    lane = chip.lanes[0]
    for n, s in enumerate(slots):
        lane.load_slot(n, s)
    lane.regs[:] = regs or [0] * 4
    lane.k[:] = k or [0] * 4
    chip.run([0])
    return chip, lane


def outputs(chip):
    return [d for _, d in chip.host_out]


def test_lowest_ready_slot_wins_and_implicit_input_check():
    chip, lane = host_lane([
        reflex(op="MOV", dst="O0", a="I0", deq=True),     # needs a token: not ready while I0 empty
        reflex(op="ADD", dst="r0", a="r0", b=1),          # always ready
    ])
    chip.run_for(10)
    assert lane.stats["fired"][0] == 0 and lane.regs[0] > 0
    chip.host_push(0x42)
    chip.run_for(10)
    assert outputs(chip) == [0x42]


def test_forwarding_keeps_tag_with_kt():
    chip, _ = host_lane([reflex(op="MOV", dst="O0", a="I0", deq=True, keep_tag=True)])
    chip.host_push(0x0123, tag=2)
    chip.run_for(10)
    assert list(chip.host_out) == [(2, 0x0123)]


def test_state_update_visible_next_clock():
    chip, lane = host_lane([
        reflex(op="ADD", dst="r0", a="r0", b=1, state=0, ns=1),
        reflex(op="ADD", dst="r1", a="r1", b=1, state=1, ns=0),
    ])
    chip.run_for(20)
    assert lane.stats["fired"][0] == lane.stats["fired"][1] == 10   # strict alternation, no gaps


def test_pending_flag_costs_exactly_one_clock():
    # slot 0 writes f0 every time it fires; slot 1 depends on f0
    chip, lane = host_lane([
        reflex(op="SUB", dst="r0", a="r0", b=1, state=0, ns=1, flag=0),
        reflex(op="ADD", dst="r1", a="r1", b=1, state=1, flags={0: 0}, ns=0),
    ], regs=[100, 0, 0, 0])
    chip.run_for(30)
    # period: slot0, (pending), slot1 -> 3 clocks per round
    assert lane.stats["fired"][0] == 10 and lane.stats["fired"][1] == 10


def test_count_loop_three_clocks_per_byte():
    """ISA.md §7.1: forward r0 bytes then report DONE; zero flag from SUB."""
    chip, lane = host_lane([
        reflex(op="MOV", dst="O0", a="I0", deq=True, state=0, flags={0: 0}, ns=1),
        reflex(op="SUB", dst="r0", a="r0", b=1, state=1, flag=0, ns=0),
        reflex(op="MOV", dst="O0", a="zero", state=0, flags={0: 1}, ot="EVENT", ns=2),
    ], regs=[8, 0, 0, 0])
    for v in range(8):
        chip.host_push(v + 1)
    starts = []
    orig = lane.compute_eval

    def spy(now):
        orig(now)
        if lane._e.get("latch", {}).get("n") == 0:
            starts.append(now)
    lane.compute_eval = spy
    chip.run_for(60)
    assert outputs(chip) == list(range(1, 9)) + [0]
    assert chip.host_out[-1][0] == 2                       # DONE is an EVENT
    gaps = {b - a for a, b in zip(starts[2:], starts[3:])}
    assert gaps == {3}, f"steady-state clocks per byte: {gaps}"


def test_call_waits_for_rb_and_routine_rate():
    """CALL implies RB == 0; a routine makes one step per 4-clock rotation."""
    body = Routine()
    body.ldi("r0", 6).label("loop").alu("ADD", "r1", "r1", 1).djnz("r0", "loop").out("O0", "r1").ret()
    chip, lane = host_lane([
        reflex(op="CALL", f=0, state=0, ns=1),
        reflex(op="CALL", f=0, state=1, ns=2),           # must wait until the first call returns
    ])
    chip.load_sram(link_routines([body]))
    chip.run_for(400)
    assert outputs(chip) == [6, 12]
    assert lane.stats["fired"][:2] == [1, 1]
    steps = 1 + 2 * 6 + 1 + 1                              # LDI, 6x(ADD, DJNZ), OUT, RET
    assert lane.stats["routine_steps"] == 2 * steps


def test_call_ignores_dst():
    """§14 L10: a CALL slot with DST = O0 neither waits for nor reserves O0."""
    chip, lane = host_lane([
        reflex(op="CALL", f=0, dst="O0", state=0, ns=1),
        reflex(op="OR", dst="O0", a="zero", b=7, state=1, ns=2),
    ])
    chip.load_sram(link_routines([Routine().ret()]))
    chip.run_for(60)
    assert outputs(chip) == [7] and lane.reserved == [0, 0]


def test_routine_step_rate_is_one_per_four_clocks():
    body = Routine().ldi("r0", 40).label("l").djnz("r0", "l").ret()
    chip, lane = host_lane([reflex(op="CALL", f=0, state=0, ns=1)])
    chip.load_sram(link_routines([body]))
    t = 0
    while lane.stats["routine_steps"] < 42 and t < 1000:
        chip.step(); t += 1
    assert lane.stats["routine_steps"] == 42
    assert 42 * 4 <= t <= 42 * 4 + 12                       # entry fetch + first fetch overhead


def test_urgent_preempts_routine_non_urgent_waits():
    body = Routine().ldi("r0", 30).label("l").djnz("r0", "l").ret()
    for urgent in (True, False):
        chip, lane = host_lane([
            reflex(op="CALL", f=0, state=0, ns=1),
            reflex(op="ADD", dst="r2", a="r2", b=1, state=1, urgent=urgent),
        ])
        chip.load_sram(link_routines([body]))
        chip.run_for(200)
        if urgent:
            assert lane.rb == 1 and lane.stats["preempted"] > 0   # routine starved by urgent slot
        else:
            assert lane.rb == 0                                   # routine finished


def test_ld_st_roundtrip():
    body = Routine().ldi("r1", 0x155).ldi("r2", 300).st("r1", "r2", 5).ld("r3", "r2", 5).out("O0", "r3").ret()
    chip, lane = host_lane([reflex(op="CALL", f=0, state=0, ns=1)])
    chip.load_sram(link_routines([body]))
    chip.run_for(200)
    assert outputs(chip) == [0x155] and chip.sram.mem[305] == 0x155


def test_output_port_throughput_one_per_three_clocks():
    """Registered release (§14 F3, Q7): reserve at EVAL, load at EXEC, consumer takes, free."""
    chip, lane = host_lane([reflex(op="ADD", dst="O0", a="r0", b=1)])
    chip.host_fifo_depth = 10_000
    chip.run_for(300)
    assert 99 <= len(chip.host_out) <= 100


def test_host_in_to_lane_one_per_two_clocks():
    chip, lane = host_lane([reflex(op="MOV", dst="r0", a="I0", deq=True)])
    for v in range(200):
        chip.host_push(v)
    chip.run_for(200)
    assert 99 <= lane.stats["fired"][0] <= 100


def test_r1_fallback_fires_every_other_clock():
    chip = Chip(lanes=1, fire_period=2)
    lane = chip.lanes[0]
    lane.load_slot(0, reflex(op="ADD", dst="r0", a="r0", b=1))
    chip.run([0])
    chip.run_for(20)
    assert lane.regs[0] == 10

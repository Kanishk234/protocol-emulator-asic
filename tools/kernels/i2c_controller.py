"""I2C controller kernel: START, repeated START, STOP, byte writes and reads, clock stretching.

Exploration firmware for tripsim (DECISIONS D-008). 11 reflex slots + 2 routines, one lane,
two pin units. As controller we generate SCL, so nothing here races a deadline: the
non-urgent START/STOP sequences run as routines from SRAM.

Host commands (tokens pushed to HOST_IN):
- EVENT data[15] = 0: START (a repeated START if the bus is ours already)
- EVENT data[15] = 1: STOP
- DATA byte: write it; the target's ACK bit (0 = ACK, 1 = NACK) comes back on HOST_OUT
- CTRL data[0] = n: read a byte and answer ACK (n = 0) or NACK (n = 1); the byte comes back

Pins: SDA = uio[sda], SCL = uio[scl], both open drain.
- SDA unit: linked shift on SCL fall (length in token); LINKED_RX on SCL rise, 8 + 1 framing,
  echo suppression; events on SDA while SCL is high reset the framing (START/STOP).
- SCL unit: CLKGEN with STRETCH; pin B = SDA, so WAIT can anchor the first clock to the
  START edge (tHD;STA = PERIOD/2).
Fabric: L.O1 feeds the SCL unit (CTRL only) and HOST_OUT (DATA only) (D-015 port filters).
"""

from kernels import load_program
from tripsim.asm import Routine, link_routines, reflex
from tripsim.isa import TAG_CTRL, TAG_DATA

IDLE, START2, BUSY, WR2, WACK, RD1, RD2, RD3 = range(8)
LEVEL0, LEVEL1 = 0x1000, 0x1800
LEN8 = WAIT_FALL = 0x7000       # DATA: 8-bit length tag / CTRL: WAIT for a falling edge
WAIT_RISE = 0x7001
CLK1, CLK8, CLK9 = 0x3001, 0x3008, 0x3009


def slots():
    free = {3: 0}                                   # f3 = RB: no routine still emitting tokens
    return [
        # START from idle: arm SCL's WAIT for the SDA fall first, then make SDA fall
        # (a WAIT must be armed before the edge it waits for)
        reflex(op="MOVB", dst="O1", a="I0", b="K1", ot="CTRL", tag="EVENT", head15=0,
               state=IDLE, flags=free, ns=START2),
        reflex(op="MOVB", dst="O0", a="I0", b="K0", ot="CTRL", tag="EVENT", head15=0, deq=True,
               state=START2, ns=BUSY),
        # repeated START / STOP: routines 0 / 1
        reflex(op="CALL", a="I0", f=0, tag="EVENT", head15=0, deq=True, state=BUSY, flags=free),
        reflex(op="CALL", a="I0", f=1, tag="EVENT", head15=1, deq=True, state=BUSY, flags=free, ns=IDLE),
        # write: SDA byte (8-bit token), 9 clocks, wait for the ACK bit
        reflex(op="OR", dst="O0", a="I0", b="K1", tag="DATA", deq=True, state=BUSY, flags=free, ns=WR2),
        reflex(op="MOVB", dst="O1", a="zero", b="K2", ot="CTRL", state=WR2, ns=WACK),
        reflex(op="MOV", dst="O1", a="I1", tag="DATA", deq=True, state=WACK, ns=BUSY),
        # read: 8 clocks, byte to the host, then our ACK/NACK bit and the 9th clock
        reflex(op="MOVB", dst="O1", a="I0", b="K3", ot="CTRL", tag="CTRL", state=BUSY, flags=free, ns=RD1),
        reflex(op="MOV", dst="O1", a="I1", tag="DATA", deq=True, state=RD1, ns=RD2),
        reflex(op="MOV", dst="O0", a="I0", ot="DATA", deq=True, state=RD2, ns=RD3),
        reflex(op="MKCTL", dst="O1", a="r0", f=0x30, state=RD3, ns=BUSY),       # CLK 1 (r0 = 1)
    ]


GAP = 0x4000


def routines(period):
    d = period // 2                                 # tSU;STA / tSU;STO = PERIOD/2 ticks
    rstart = Routine()
    rstart.ldi("r1", 1).out("O0", "r1", "DATA")                     # SDA: release at the next fall
    rstart.load16("r2", CLK1).out("O1", "r2", "CTRL")                # SCL: one clock (ends high)
    rstart.load16("r2", WAIT_FALL).out("O1", "r2", "CTRL")           # SCL: arm WAIT for the START edge
    rstart.load16("r2", WAIT_RISE).out("O0", "r2", "CTRL")           # SDA: wait for SCL high
    rstart.load16("r2", LEVEL0 | d).out("O0", "r2", "CTRL").ret()     # SDA falls: repeated START
    stop = Routine()
    stop.ldi("r1", 0).out("O0", "r1", "DATA")                        # SDA: low at the next fall
    stop.load16("r2", CLK1).out("O1", "r2", "CTRL")
    stop.load16("r2", WAIT_RISE).out("O0", "r2", "CTRL")
    stop.load16("r2", LEVEL1 | d).out("O0", "r2", "CTRL")            # SDA rises: STOP
    stop.load16("r2", GAP | period).out("O0", "r2", "CTRL").ret()    # bus free time (tBUF) before a START
    return [rstart, stop]


def load(chip, period, lane=0, units=(0, 1), sda=0, scl=1):
    """Load programs/i2c_controller.trw; period: SCL period in clocks (even, >= 8)."""
    if (lane, tuple(units), sda, scl) != (0, (0, 1), 0, 1):
        raise ValueError("pin placement is fixed in programs/i2c_controller.trw")
    if period // 2 > 0x3FF:
        raise ValueError("period too long for the LEVEL delay in this program")
    image = load_program(chip, "i2c_controller", PERIOD=period)
    return len(image["lanes"]["L0"]["slots"])

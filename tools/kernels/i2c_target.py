"""I2C target kernel, read and write: address match, ACK/NACK, bytes to and from the host.

Exploration firmware for tripsim (DECISIONS D-008), assembled with tripsim.asm. It will
be rewritten as programs/i2c_target.trw once tripc exists. 12 reflex slots, one lane,
one pin unit, using only general pin-unit primitives (D-012, D-013):
- event generator: edges of SDA while SCL is high -> START (SDA new level 0) / STOP (1),
  and each event restarts word framing;
- LINKED_RX on SCL rise, two-phase framing 8 + 1 bits (byte, then the ACK/NACK bit);
- echo suppression: words sampled while we drive SDA (our ACKs, our read bytes) are
  dropped by the pin unit, so the firmware only sees the other side's bits;
- TX linked shift on SCL fall, open drain, length in the token (ACK = 1 bit, byte = 8).

Wiring: L.I0 <- U.rx; L.I1 <- HOST_IN (bytes to send on reads); L.O0 -> U.tx;
L.O1 -> HOST_OUT (bytes received on writes). No clock stretching: read data must be
waiting in HOST_IN before the controller asks for it.
"""

from tripsim import PAD_UIO
from tripsim.asm import cmpm_field, reflex

IDLE, ADDR, ACKQ, RW, XFER, FWD, RT = range(7)
LEN8 = 0x7000                  # TX length-in-token: 8 bits


def slots():
    U = True
    return [
        # 0-1: START / STOP from any state (lowest indices win)
        reflex(urgent=U, op="MOV", a="I0", tag="EVENT", head15=0, deq=True, ns=ADDR),
        reflex(urgent=U, op="MOV", a="I0", tag="EVENT", head15=1, deq=True, ns=IDLE),
        # 2: address byte: f0 = our address (R/W bit masked off); keep the byte for R/W
        reflex(urgent=U, op="CMPM", a="I0", f=cmpm_field("K0", "K1"), flag=0,
               state=ADDR, tag="DATA", ns=ACKQ),
        # 3: ours -> ACK (a 1-bit token of value 0), still holding the byte
        reflex(urgent=U, op="MOVB", dst="O0", a="I0", b=0, state=ACKQ, flags={0: 1}, ns=RW),
        # 4: not ours -> drop it and ignore the bus until the next START
        reflex(urgent=U, op="MOV", a="I0", deq=True, state=ACKQ, flags={0: 0}, ns=IDLE),
        # 5: f1 = write (R/W bit is 0)
        reflex(urgent=U, op="AND", a="I0", b=1, flag=1, deq=True, state=RW, ns=XFER),
        # 6-7: write: ACK the byte first (peek), then forward it to the host
        reflex(urgent=U, op="MOVB", dst="O0", a="I0", b=0, tag="DATA",
               state=XFER, flags={1: 1}, ns=FWD),
        reflex(op="MOV", dst="O1", a="I0", deq=True, state=FWD, ns=XFER),
        # 8: read: send the next host byte (8-bit token); SDA is released for the ACK clock
        reflex(urgent=U, op="OR", dst="O0", a="I1", b="K2", deq=True,
               state=XFER, flags={1: 0}, ns=RT),
        # 9-10: the controller's ACK (data[0] = 0): send more; NACK: done
        reflex(urgent=U, op="MOV", a="I0", tag="DATA", head0=0, deq=True, state=RT, ns=XFER),
        reflex(urgent=U, op="MOV", a="I0", tag="DATA", head0=1, deq=True, state=RT, ns=IDLE),
        # 11: not addressed: drop bus traffic
        reflex(op="MOV", a="I0", tag="DATA", deq=True, state=IDLE),
    ]


def load(chip, addr, lane=0, unit=0, sda=0, scl=1):
    """Configure the chip as an I2C target at 7-bit `addr`."""
    chip.pin_config(unit, pin_a=PAD_UIO + sda, pin_b=PAD_UIO + scl,
                    rxmode="linked_rx", rx_edge="rise", rx_nbits=8, rx_nbits2=1, order="msb",
                    ev_edge="both", ev_qual=1, ev_reset=True, rx_echo=False,
                    txmode="shift", tx_edge="fall", tx_lentok=True, od=True, idle=1)
    chip.own(PAD_UIO + sda, unit)
    chip.connect(f"L{lane}.I0", f"U{unit}.rx")
    chip.connect(f"L{lane}.I1", "HOST_IN")
    chip.connect(f"U{unit}.tx", f"L{lane}.O0")
    chip.connect("HOST_OUT", f"L{lane}.O1")
    ln = chip.lanes[lane]
    ln.k[:] = [0x00FE, addr << 1, LEN8, 0]
    for n, s in enumerate(slots()):
        ln.load_slot(n, s)
    chip.run([lane])
    return len(slots())

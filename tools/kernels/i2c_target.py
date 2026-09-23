"""I2C target kernel (write direction): address match, ACK, received bytes to the host.

Exploration firmware for tripsim (DECISIONS D-008), assembled with tripsim.asm. It will
be rewritten as programs/i2c_target_eeprom.trw once tripc exists.

Wiring: SDA = uio[sda], SCL = uio[scl], one pin unit, one lane.
- Pin unit: LINKED_RX (8 bits MSB-first on SCL rise, plus a tail token for the 9th/ACK
  bit), COND_EDGE (START/STOP), TX linked shift on SCL fall, open drain.
- L.I0 <- U.rx (blocking); L.O0 -> U.tx (ACK bits); L.O1 -> HOST_OUT (received bytes).

Token stream per transaction: EVENT START, DATA address, DATA tail, {DATA byte, DATA tail}*,
EVENT STOP. A tail token carries the sampled 9th bit in data[15] (here: our own ACK).
"""

from tripsim import PAD_UIO
from tripsim.asm import cmpm_field, reflex

IDLE, ADDR, ACKQ, TAIL, WR, FWD = range(6)


def slots():
    return [
        # START / STOP from any state (lowest indices: highest priority)
        reflex(urgent=True, op="MOV", a="I0", tag="EVENT", head15=1, deq=True, ns=ADDR),
        reflex(urgent=True, op="MOV", a="I0", tag="EVENT", head15=0, deq=True, ns=IDLE),
        # address byte: f0 = (byte & K0) == K1   (K1 = our address, write bit 0)
        reflex(urgent=True, op="CMPM", a="I0", f=cmpm_field("K0", "K1"), flag=0,
               state=ADDR, tag="DATA", deq=True, ns=ACKQ),
        reflex(urgent=True, op="MOV", dst="O0", a="zero", state=ACKQ, flags={0: 1}, ns=TAIL),   # ACK bit
        reflex(urgent=True, op="MOV", a="zero", state=ACKQ, flags={0: 0}, ns=IDLE),            # not us
        # the tail token after each ACK clock is our own ACK read back: drop it
        reflex(urgent=True, op="MOV", a="I0", state=TAIL, tag="DATA", deq=True, ns=WR),
        # data byte: ACK first (MOVB: peek the byte, send DATA 0), then forward it to the host
        reflex(urgent=True, op="MOVB", dst="O0", a="I0", b=0, state=WR, tag="DATA", ns=FWD),
        reflex(op="MOV", dst="O1", a="I0", state=FWD, tag="DATA", deq=True, ns=TAIL),
        # not addressed: drop bus traffic until the next START
        reflex(op="MOV", a="I0", state=IDLE, tag="DATA", deq=True),
    ]


def load(chip, addr, lane=0, unit=0, sda=0, scl=1):
    """Configure the chip as an I2C target at 7-bit `addr` (write direction only)."""
    chip.pin_config(unit, pin_a=PAD_UIO + sda, pin_b=PAD_UIO + scl,
                    rxmode="linked_rx", cond_edge=True, rx_edge="rise", rx_nbits=8, rx_tail=1,
                    order="msb", txmode="shift", tx_edge="fall", nbits=1, od=True, idle=1)
    chip.own(PAD_UIO + sda, unit)
    chip.connect(f"L{lane}.I0", f"U{unit}.rx")
    chip.connect(f"U{unit}.tx", f"L{lane}.O0")
    chip.connect("HOST_OUT", f"L{lane}.O1")
    ln = chip.lanes[lane]
    ln.k[:] = [0x00FF, addr << 1, 0, 0]
    for n, s in enumerate(slots()):
        ln.load_slot(n, s)
    chip.run([lane])
    return len(slots())

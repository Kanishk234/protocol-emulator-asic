"""SPI target kernel, mode 0, MSB first: TRIPWIRE as the peripheral. 3 slots, 2 pin units.

Exploration firmware for tripsim (DECISIONS D-008).

- Bytes received on MOSI go to the host (HOST_OUT), framed by CS events:
  EVENT data[15] = 0 at select (CS fell), 1 at deselect.
- Bytes the host pushes (HOST_IN) are sent on MISO, one per byte clocked in. A byte is
  pre-loaded while CS is high, so bit 7 is ready at the first SCK rise; MISO is driven
  only while selected (tri-state otherwise). Deselect aborts a byte in progress.

Pins: MOSI = ui[mosi], SCK = ui[sck], CS = ui[cs], MISO = uio[miso].
Unit RX: A = MOSI, B = SCK, C = CS (LINKED_RX on SCK rise, framing held while
deselected, events on C). Unit TX: A = MISO, B = SCK, C = CS (linked shift on SCK
fall, preload, length in token, OE only while selected).
"""

from kernels import load_program
from tripsim.asm import reflex

LEN8 = 0x7000


def slots():
    return [
        reflex(op="MOV", dst="O1", a="I0", tag="EVENT", deq=True, keep_tag=True),   # CS markers
        reflex(op="MOV", dst="O1", a="I0", tag="DATA", deq=True),                   # MOSI byte
        reflex(op="OR", dst="O0", a="I1", b="K0", deq=True),                       # next MISO byte
    ]


def load(chip, lane=0, units=(0, 1), mosi=0, sck=1, cs=2, miso=0, miso_edge="rise"):
    """Load programs/spi_target.trw. miso_edge: SCK edge on which MISO moves to the next bit.
    Mode 0 samples on the rise, so changing right after it ("rise") gives the bit a full
    period to settle; "fall" is the textbook choice and halves the maximum SCK."""
    if (lane, tuple(units), mosi, sck, cs, miso) != (0, (0, 1), 0, 1, 2, 0):
        raise ValueError("pin placement is fixed in programs/spi_target.trw")
    image = load_program(chip, "spi_target", MISO_EDGE=miso_edge)
    return len(image["lanes"]["L0"]["slots"])

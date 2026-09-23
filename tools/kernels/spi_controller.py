"""SPI controller kernel, mode 0, MSB first. One lane, four pin units.

Exploration firmware for tripsim (DECISIONS D-008), to become programs/spi_ctrl.trw.

Host protocol (tokens pushed to HOST_IN):
- EVENT with data[0] = level: drive CS (0 = select, 1 = deselect);
- DATA byte: transfer one byte; the byte read on MISO comes back on HOST_OUT.

Pins: SCK = uo[sck] (CLKGEN), MOSI = uo[mosi] (shift linked to our SCK fall, bit 0
preloaded), CS = uo[cs] (LEVEL), MISO = ui[miso] (LINKED_RX on our SCK rise).

One lane output feeds three pin units (D-011): L.O0 is multicast to SCK, MOSI and CS,
and each unit's tag filter picks its tokens (SCK: CTRL, MOSI: DATA, CS: EVENT). MISO
bytes come back through the lane (L.I1), so CS can only rise after the last byte is in.
"""

from kernels import load_program
from tripsim.asm import reflex
from tripsim.isa import TAG_CTRL, TAG_DATA, TAG_EVENT

IDLE, CLK, WAITRX = range(3)
CLK8 = 0x3008                 # CTRL CLK, n = 8


def slots():
    return [
        reflex(op="MOV", dst="O0", a="I0", tag="DATA", deq=True, keep_tag=True, state=IDLE, ns=CLK),
        reflex(op="MOVB", dst="O0", a="zero", b="K0", ot="CTRL", state=CLK, ns=WAITRX),
        reflex(op="MOV", dst="O1", a="I1", tag="DATA", deq=True, state=WAITRX, ns=IDLE),
        reflex(op="MOV", dst="O0", a="I0", tag="EVENT", deq=True, keep_tag=True, state=IDLE),
    ]


def load(chip, period, lane=0, sck=0, mosi=1, cs=2, miso=0, units=(0, 1, 2, 3)):
    """Load programs/spi_controller.trw; period: SCK period in clocks (>= 2)."""
    if (lane, sck, mosi, cs, miso, tuple(units)) != (0, 0, 1, 2, 0, (0, 1, 2, 3)):
        raise ValueError("pin placement is fixed in programs/spi_controller.trw")
    image = load_program(chip, "spi_controller", PERIOD=period)
    return len(image["lanes"]["L0"]["slots"])


def push_transfer(chip, data):
    chip.host_push(0, tag=TAG_EVENT)          # CS low
    for b in data:
        chip.host_push(b, tag=TAG_DATA)
    chip.host_push(1, tag=TAG_EVENT)          # CS high

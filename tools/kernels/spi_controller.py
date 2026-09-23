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

from tripsim import PAD_UI, PAD_UO
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
    """period: SCK period in clocks (>= 2)."""
    u_sck, u_mosi, u_miso, u_cs = units
    chip.pin_config(u_sck, pin_a=PAD_UO + sck, txmode="clkgen", period=period, idle=0)
    chip.pin_config(u_mosi, pin_a=PAD_UO + mosi, pin_b=PAD_UO + sck, txmode="shift",
                    tx_edge="fall", tx_preload=True, nbits=8, order="msb", idle=0)
    chip.pin_config(u_cs, pin_a=PAD_UO + cs, txmode="level", idle=1)
    chip.pin_config(u_miso, pin_a=PAD_UI + miso, pin_b=PAD_UO + sck, rxmode="linked_rx",
                    rx_edge="rise", rx_nbits=8, order="msb")
    for pad, unit in ((sck, u_sck), (mosi, u_mosi), (cs, u_cs)):
        chip.own(PAD_UO + pad, unit)
    # one lane output multicast to three pin units; each port keeps only its tag (D-015)
    for unit, tag in ((u_sck, TAG_CTRL), (u_mosi, TAG_DATA), (u_cs, TAG_EVENT)):
        chip.connect(f"U{unit}.tx", f"L{lane}.O0", accept=1 << tag)
    chip.connect(f"L{lane}.I0", "HOST_IN")
    chip.connect(f"L{lane}.I1", f"U{u_miso}.rx")
    chip.connect("HOST_OUT", f"L{lane}.O1")
    ln = chip.lanes[lane]
    ln.k[:] = [CLK8, 0, 0, 0]
    for n, s in enumerate(slots()):
        ln.load_slot(n, s)
    chip.run([lane])
    return len(slots())


def push_transfer(chip, data):
    chip.host_push(0, tag=TAG_EVENT)          # CS low
    for b in data:
        chip.host_push(b, tag=TAG_DATA)
    chip.host_push(1, tag=TAG_EVENT)          # CS high

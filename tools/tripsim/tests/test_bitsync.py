"""BITSYNC primitives (D-023) in a non-CAN configuration, to keep them general:
HDLC-style stuffing (a 0 after five 1s, ones only), CRC-16/CCITT, LSB-first words, a drifting
transmitter, readback and the one-bit override. §14 P20-P26."""

import pytest

from tripsim import PAD_UI, PAD_UO, Chip
from tripsim.isa import TAG_CTRL, TAG_DATA, TAG_ERR, TAG_EVENT

CCITT = 0x1021
PERIOD = 40
HDLC = dict(txmode="bitsync", rxmode="bitsync", period=PERIOD, sampleofs=0.5, sjw=PERIOD / 4,
            idle=1, idle_bits=8, order="lsb", rx_nbits=8, nbits=8, stuff_n=5, stuff_lvl=1,
            crc_width=16, crc_poly=CCITT, crc_init=0xFFFF, crc_res=0)


def crc_ccitt(bits, crc=0xFFFF):
    for b in bits:
        top = (crc >> 15) & 1
        crc = (crc << 1) & 0xFFFF
        if top ^ b:
            crc ^= CCITT
    return crc


def line_frame(payload, start=(0,)):
    """Reference encoder: start bit(s), bytes LSB first, CRC MSB first, ones-only stuffing."""
    bits = list(start) + [(byte >> i) & 1 for byte in payload for i in range(8)]
    crc = crc_ccitt(bits)
    bits += [(crc >> (15 - i)) & 1 for i in range(16)]
    out, run = [], 0
    for b in bits:
        out.append(b)
        run = run + 1 if b == 1 else 0
        if run == 5:
            out.append(0)
            run = 0
    return out, bits


def rx_chip():
    chip = Chip(lanes=1)
    chip.settle_inputs(ui=1)
    chip.pin_config(0, pin_a=PAD_UO + 0, pin_s=PAD_UI + 0, **HDLC)
    chip.own(PAD_UO + 0, 0)
    chip.connect("U0.tx", "HOST_IN")
    chip.connect("HOST_OUT", "U0.rx")
    return chip


def drive(chip, line_bits, period, lead=10):
    """A transmitter with its own (possibly drifting) clock, idle high around the frame."""
    t, levels = 0.0, []
    for b in [1] * lead + line_bits + [1] * 12:
        n = round(t + period) - round(t)
        levels += [b] * n
        t += period
    for v in levels:
        chip.ui_in = v
        chip.step()


@pytest.mark.parametrize("drift", [1.0, 1.02, 0.98])       # ±2 % transmitter clock
def test_hdlc_style_receive_with_ones_stuffing_crc16_and_drift(drift):
    payload = [0xFF, 0x7E, 0x00, 0xF8, 0x1F]                # long runs of ones force stuffing
    line, bits = line_frame(payload)
    assert len(line) > len(bits)                             # the premise: stuffing happened
    chip = rx_chip()
    chip.host_push(0x9000 | 0x800 | len(bits), tag=TAG_CTRL)  # FRAME (next): start + 5 bytes + CRC
    chip.run_for(20)
    drive(chip, line, PERIOD * drift)
    out = list(chip.host_out)
    # LSB-first 8-bit words: the start bit shifts the bytes by one position
    word_bits = [b for t, d in out if t == TAG_DATA for b in ((d >> i) & 1 for i in range(8))]
    assert len(word_bits) == len(bits) // 8 * 8 and word_bits == bits[:len(word_bits)]
    assert out[-1] == (TAG_EVENT, bits[-1])                   # last partial word; CRC-16 residue good


def test_hdlc_style_crc_error_and_stuff_error():
    line, bits = line_frame([0x12, 0x34])
    bad = line[:]
    bad[5] ^= 1                                              # a data bit flipped: CRC error
    chip = rx_chip()
    chip.host_push(0x9800 | len(bits), tag=TAG_CTRL)
    chip.run_for(20)
    drive(chip, bad, PERIOD)
    assert list(chip.host_out)[-1][0] == TAG_ERR and list(chip.host_out)[-1][1] >> 12 == 0
    chip = rx_chip()
    chip.host_push(0x9800 | 40, tag=TAG_CTRL)
    chip.run_for(20)
    drive(chip, [0] + [1] * 7, PERIOD)                       # six 1s: a missing stuff bit
    errs = [d for t, d in chip.host_out if t == TAG_ERR]
    assert errs and errs[0] >> 12 == 1


def test_tx_stuffing_crc_append_matches_reference_encoder():
    chip = Chip(lanes=1)
    chip.settle_inputs(ui=1)
    chip.pin_config(0, pin_a=PAD_UO + 0, pin_s=PAD_UO + 0, tx_lentok=True, **HDLC)
    chip.own(PAD_UO + 0, 0)
    chip.connect("U0.tx", "HOST_IN")
    chip.connect("HOST_OUT", "U0.rx")
    chip.run_for(12 * PERIOD)                                # bus idle
    payload = [0xFF, 0x3C]
    chip.host_push(0x5000, tag=TAG_CTRL)                     # SYNC: a new frame at bus idle
    chip.host_push(0xA004, tag=TAG_CTRL)                     # LINE: stuffing on
    chip.host_push(0x0000)                                   # start bit (1 bit: 0)
    for b in payload:
        chip.host_push(0x7000 | b)
    chip.host_push(0xA00C, tag=TAG_CTRL)                     # LINE: stuffing on, append CRC
    chip.host_push(0xA000, tag=TAG_CTRL)
    trace = []
    for i in range(40 * PERIOD):
        if i == 16 * PERIOD:                                 # mid-frame: an override is ignored
            chip.host_push(0xB000, tag=TAG_CTRL)             # in a frame we transmit ourselves
        chip.step()
        trace.append(chip.outputs()[0] & 1)
    start = trace.index(0)
    sampled = [trace[start + PERIOD // 2 + k * PERIOD] for k in range(len(line_frame(payload)[0]))]
    assert sampled == line_frame(payload)[0]
    assert chip.pins[0].bs.jam is None                  # it was consumed, not applied


def test_override_drives_exactly_one_bit_in_another_nodes_frame():
    """(The own-frame case is in the TX test above: the override is ignored there.)"""
    line, bits = line_frame([0x55])
    chip = rx_chip()
    chip.host_push(0x9800 | len(bits), tag=TAG_CTRL)
    chip.run_for(20)
    seen = {"low_while_line_high": 0}

    def run_line(bits_on_line):
        levels = []
        for b in [1] * 10 + bits_on_line + [1] * 12:
            levels += [b] * PERIOD
        return levels

    levels = run_line(line)
    for i, v in enumerate(levels):
        if i == 10 * PERIOD + 3 * PERIOD:
            chip.host_push(0xB000, tag=TAG_CTRL)             # JAM: dominant (0) for one bit, now
        chip.ui_in = v
        chip.step()
        if (chip.outputs()[0] & 1) == 0:
            seen["low_while_line_high"] += 1
    assert PERIOD - 2 <= seen["low_while_line_high"] <= PERIOD + 2   # exactly one bit

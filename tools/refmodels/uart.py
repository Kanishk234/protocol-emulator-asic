"""UART reference model: asynchronous serial frames, LSB first, idle high.

Written from the UART framing definition (start bit 0, data bits LSB first, optional parity,
stop bit(s) 1), independent of any WARP RTL.

Waveforms are lists of line levels, one entry per system clock. A bit lasts `cpb`
(clocks per bit) entries.
"""

from dataclasses import dataclass
from typing import List, Optional, Sequence


@dataclass(frozen=True)
class Frame:
    data: int
    framing_ok: bool  # stop bit(s) read as 1
    parity_ok: Optional[bool] = None  # None when no parity is used


def frame_bits(data: int, nbits: int = 8, parity: Optional[str] = None, stop: int = 1) -> List[int]:
    """Line levels, one per bit time, for one frame: start, data LSB first, parity, stop."""
    if not 0 <= data < (1 << nbits):
        raise ValueError(f"data {data:#x} does not fit in {nbits} bits")
    if parity not in (None, "even", "odd"):
        raise ValueError(f"parity must be None, 'even' or 'odd', not {parity!r}")
    if stop not in (1, 2):
        raise ValueError("stop must be 1 or 2")
    bits = [0] + [(data >> i) & 1 for i in range(nbits)]
    if parity is not None:
        ones = bin(data).count("1")
        bits.append(ones & 1 if parity == "even" else 1 - (ones & 1))
    bits += [1] * stop
    return bits


def encode(data: Sequence[int], cpb: int, nbits: int = 8, parity: Optional[str] = None,
           stop: int = 1, idle_before: int = 0, gap: int = 0) -> List[int]:
    """Waveform (one level per clock) for back-to-back frames, with `gap` idle clocks between them."""
    if cpb < 1:
        raise ValueError("cpb must be >= 1")
    wave = [1] * idle_before
    for i, byte in enumerate(data):
        for level in frame_bits(byte, nbits, parity, stop):
            wave += [level] * cpb
        if i != len(data) - 1:
            wave += [1] * gap
    return wave


def decode(wave: Sequence[int], cpb: int, nbits: int = 8, parity: Optional[str] = None,
           stop: int = 1) -> List[Frame]:
    """Decode a waveform the way a receiver samping mid-bit would.

    A frame starts at a 1->0 transition (or a 0 at index 0). Each bit is sampled at the
    middle of its bit time. A start bit that is 1 at its middle is a glitch and is skipped.
    After a frame, the search for the next start resumes after the first stop bit's middle.
    """
    frames: List[Frame] = []
    i = 0
    n = len(wave)
    prev = 1
    while i < n:
        level = wave[i]
        if prev == 1 and level == 0:
            mid = i + cpb // 2
            if mid >= n:
                break
            if wave[mid] != 0:  # glitch, not a start bit
                prev = level
                i += 1
                continue
            samples = []
            nsamp = nbits + (1 if parity else 0) + stop
            ok = True
            for k in range(1, nsamp + 1):
                t = mid + k * cpb
                if t >= n:
                    ok = False
                    break
                samples.append(wave[t])
            if not ok:
                break
            data = sum(b << j for j, b in enumerate(samples[:nbits]))
            pos = nbits
            parity_ok = None
            if parity is not None:
                ones = bin(data).count("1") + samples[pos]
                parity_ok = (ones % 2 == 0) if parity == "even" else (ones % 2 == 1)
                pos += 1
            framing_ok = all(b == 1 for b in samples[pos:pos + stop])
            frames.append(Frame(data, framing_ok, parity_ok))
            i = mid + (nbits + (1 if parity else 0) + 1) * cpb  # middle of the first stop bit
            prev = wave[i] if i < n else 1
            i += 1
            continue
        prev = level
        i += 1
    return frames

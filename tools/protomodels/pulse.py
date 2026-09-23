"""Reference decoders for pulse-width-coded LED and motor protocols (one level per 50 MHz clock).

Written from the protocol definitions, not from TRIPWIRE firmware:
- WS2812B datasheet: T0H 0.40 us, T1H 0.80 us, T0L 0.85 us, T1L 0.45 us (each +-150 ns),
  TH + TL = 1.25 us +- 600 ns, RESET = low for more than 50 us. 24 bits per LED, G-R-B, MSB first.
- DShot: 16-bit frames, MSB first: 11-bit throttle, 1 telemetry-request bit, 4-bit checksum
  (v ^ v >> 4 ^ v >> 8) & 0xF with v = throttle << 1 | telemetry. T1H = 75 %, T0H = 37.5 %
  of the bit period (DShot600: 1.667 us).
"""

NS = 20  # ns per clock


def runs(levels):
    out = []
    for v in levels:
        if out and out[-1][0] == v:
            out[-1][1] += 1
        else:
            out.append([v, 1])
    return out


def ws2812_decode(levels):
    """Returns (frames, violations): frames = [[byte, ...], ...] split at RESET (low > 50 us)."""
    frames, frame, bits, errs = [], [], [], []
    r = runs(levels)
    i = 0
    while i < len(r) and r[i][0] == 0:
        i += 1
    while i + 1 < len(r) or (i < len(r) and r[i][0] == 1):
        (hv, hn) = r[i]
        ln = r[i + 1][1] if i + 1 < len(r) else 10**9
        th, tl = hn * NS, ln * NS
        if 250 <= th <= 550:
            bit, tl_ok = 0, (700 <= tl <= 1000)
        elif 650 <= th <= 950:
            bit, tl_ok = 1, (300 <= tl <= 600)
        else:
            errs.append(f"high {th} ns at run {i} is neither T0H nor T1H")
            bit, tl_ok = None, True
        reset = tl > 50_000
        if bit is not None:
            bits.append(bit)
            if not reset and not tl_ok:
                errs.append(f"low {tl} ns after a {bit} bit")
            if not reset and not 650 <= th + tl <= 1850:
                errs.append(f"bit period {th + tl} ns")
        if len(bits) == 8:
            frame.append(sum(b << (7 - k) for k, b in enumerate(bits)))
            bits = []
        if reset:
            if bits:
                errs.append(f"{len(bits)} stray bits before RESET")
            frames.append(frame)
            frame, bits = [], []
        i += 2
    if frame:
        frames.append(frame)
    return frames, errs


def dshot_crc(v):
    return (v ^ (v >> 4) ^ (v >> 8)) & 0x0F


def dshot_decode(levels, bit_clocks):
    """Returns (frames, violations): frames = [(throttle, telemetry, crc_ok), ...]."""
    frames, bits, errs = [], [], []
    r = runs(levels)
    i = 0
    while i < len(r) and r[i][0] == 0:
        i += 1
    while i < len(r):
        hn = r[i][1]
        ln = r[i + 1][1] if i + 1 < len(r) else 10**9
        duty = hn / bit_clocks
        if abs(duty - 0.375) <= 0.06:
            bits.append(0)
        elif abs(duty - 0.75) <= 0.06:
            bits.append(1)
        else:
            errs.append(f"high {hn} clocks = {duty:.0%} of a bit")
        gap = ln > 1.5 * bit_clocks
        if not gap and abs(hn + ln - bit_clocks) > 0.05 * bit_clocks:
            errs.append(f"bit period {hn + ln} clocks, expected {bit_clocks:.1f}")
        if gap:
            if len(bits) != 16:
                errs.append(f"frame of {len(bits)} bits")
            else:
                w = sum(b << (15 - k) for k, b in enumerate(bits))
                v = w >> 4
                frames.append((v >> 1, v & 1, dshot_crc(v) == (w & 0xF)))
            bits = []
        i += 2
    return frames, errs

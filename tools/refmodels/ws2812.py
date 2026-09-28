"""WS2812 / WS2812B data line: independent reference decoder (held-out protocol H1, phase 4).

Written from the WS2812B datasheet (Worldsemi, rev. V5), not from any WARP design:
  - one bit = a high pulse then a low time; T0H = 0.4 us, T1H = 0.8 us (each +-150 ns),
    T0L = 0.85 us, T1L = 0.45 us (+-150 ns); the bit period (TH + TL) is 1.25 us +-600 ns;
  - bits are sent MSB first, 24 per LED in G, R, B order; each LED keeps its first 24 bits and
    passes the rest on;
  - RES: the line low for more than 50 us latches the data (newer WS2812B revisions need
    > 280 us; `reset_ns` selects).

`decode(samples, clk_ns)` takes the line sampled once per system clock and returns the frames
(lists of bytes between reset gaps) and a list of timing violations. It never guesses: a pulse
outside both high-time windows, or a bit period outside its window, is a violation.
"""

T0H = (250, 550)          # ns, 0.40 us +-150
T1H = (650, 950)          # ns, 0.80 us +-150
PERIOD = (650, 1850)      # ns, 1.25 us +-600
RESET_NS = 50_000


def decode(samples, clk_ns, reset_ns=RESET_NS):
    frames, errors = [], []
    bits = []

    def close_frame(at):
        if bits:
            if len(bits) % 8:
                errors.append((at, "frame of %d bits is not whole bytes" % len(bits)))
            frames.append([int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits) - len(bits) % 8, 8)])
            bits.clear()

    n = len(samples)
    i = 0
    # skip the initial level up to the first rising edge
    while i < n and samples[i] == 1:
        i += 1
    last_rise = None
    while i < n:
        # low run
        j = i
        while j < n and samples[j] == 0:
            j += 1
        low_ns = (j - i) * clk_ns
        if j >= n:
            if low_ns >= reset_ns:
                close_frame(i)
            break
        if low_ns >= reset_ns:
            close_frame(i)
            last_rise = None
        # high run
        k = j
        while k < n and samples[k] == 1:
            k += 1
        if k >= n:
            errors.append((j, "line ends high"))
            break
        high_ns = (k - j) * clk_ns
        if last_rise is not None:
            period = (j - last_rise) * clk_ns
            if not PERIOD[0] <= period <= PERIOD[1]:
                errors.append((j, "bit period %d ns" % period))
        if T0H[0] <= high_ns <= T0H[1]:
            bits.append(0)
        elif T1H[0] <= high_ns <= T1H[1]:
            bits.append(1)
        else:
            errors.append((j, "high time %d ns is neither a 0 nor a 1" % high_ns))
        last_rise = j
        i = k
    return frames, errors


def encode(data, clk_ns, t0h=400, t1h=800, period=1250, reset_ns=RESET_NS, lead_ns=RESET_NS):
    """An ideal waveform (one sample per clock) for bytes `data`: for tests of the decoder."""
    c = lambda ns: max(1, round(ns / clk_ns))
    out = [0] * c(lead_ns)
    for b in data:
        for k in range(7, -1, -1):
            h = c(t1h if (b >> k) & 1 else t0h)
            out += [1] * h + [0] * (c(period) - h)
    return out + [0] * c(reset_ns)

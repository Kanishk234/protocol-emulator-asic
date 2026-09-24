"""Reference NEC infrared protocol model, written from the NEC IR transmission format
(as documented for the uPD6121 family), not from TRIPWIRE firmware.

Timing (in 50 MHz clocks): leader 9 ms mark + 4.5 ms space; bit 0 = 562.5 us mark + 562.5 us
space; bit 1 = 562.5 us mark + 1687.5 us space; final 562.5 us mark. 32 bits LSB first:
address, ~address, command, ~command. Repeat code: 9 ms mark + 2.25 ms space + mark.
"""

US = 50
MARK = 562.5 * US


def envelope(addr, cmd, repeats=0, active_low=True, idle_us=2000):
    """Demodulated receiver output (active low by default), one value per clock."""
    on, off = (0, 1) if active_low else (1, 0)
    level, t = [], 0.0

    def emit(v, clocks):
        nonlocal t
        start, t = round(t), t + clocks
        level.extend([v] * (round(t) - start))

    emit(off, idle_us * US)
    emit(on, 9000 * US)
    emit(off, 4500 * US)
    bits = [(b >> i) & 1 for b in (addr, addr ^ 0xFF, cmd, cmd ^ 0xFF) for i in range(8)]
    for b in bits:
        emit(on, MARK)
        emit(off, 3 * MARK if b else MARK)
    emit(on, MARK)
    for _ in range(repeats):
        emit(off, 40000 * US)
        emit(on, 9000 * US)
        emit(off, 2250 * US)
        emit(on, MARK)
    emit(off, idle_us * US)
    return level


def decode_modulated(samples, carrier_clocks):
    """Decode an active-high, carrier-modulated LED drive signal. Returns (frames, marks):
    frames = [(addr, cmd)] with the complement bytes checked; marks = [(start, length)]."""
    gap = 2 * carrier_clocks                       # longer low than this ends a mark
    marks, i, n = [], 0, len(samples)
    while i < n:
        if samples[i]:
            start, last = i, i
            while i < n and i - last <= gap:
                if samples[i]:
                    last = i
                i += 1
            marks.append((start, last + 1 - start))
        i += 1
    frames, k = [], 0
    while k < len(marks):
        s, length = marks[k]
        if abs(length - 9000 * US) < 200 * US and k + 33 < len(marks):
            space = marks[k + 1][0] - (s + length)
            if abs(space - 4500 * US) < 300 * US:
                bits = []
                for j in range(32):
                    ms, ml = marks[k + 1 + j]
                    sp = marks[k + 2 + j][0] - (ms + ml)
                    bits.append(1 if sp > 2 * MARK else 0)
                val = [sum(bits[8 * q + i] << i for i in range(8)) for q in range(4)]
                assert val[1] == val[0] ^ 0xFF and val[3] == val[2] ^ 0xFF
                frames.append((val[0], val[2]))
                k += 34
                continue
        k += 1
    return frames, marks

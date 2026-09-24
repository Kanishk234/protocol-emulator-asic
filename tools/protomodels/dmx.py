"""Reference DMX512-A line model (ANSI E1.11), written from the standard, not from TRIPWIRE firmware.

A packet: BREAK (low, >= 88 us), MARK AFTER BREAK (high, >= 8 us), then up to 513 slots,
each an asynchronous frame at 250 kbaud: start bit 0, 8 data bits LSB first, 2 stop bits 1.
The first slot is the start code (0 for dimmer data). Levels: one value per 50 MHz clock.
"""

CLK = 50e6
BIT = CLK / 250_000                    # 200 clocks


def encode(packets, break_us=100, mab_us=12, idle_us=20):
    level, t = [], 0.0

    def emit(v, clocks):
        nonlocal t
        start, t = round(t), t + clocks
        level.extend([v] * (round(t) - start))

    emit(1, idle_us * 50)
    for slots in packets:
        emit(0, break_us * 50)
        emit(1, mab_us * 50)
        for byte in slots:
            emit(0, BIT)
            for k in range(8):
                emit((byte >> k) & 1, BIT)
            emit(1, 2 * BIT)
    emit(1, idle_us * 50)
    return level


def decode(samples):
    """[(break_us, mab_us, [slots])] with every frame's stop bits checked."""
    out, i, n = [], 1, len(samples)
    while i < n:
        if samples[i - 1] == 1 and samples[i] == 0:
            j = i
            while j < n and samples[j] == 0:
                j += 1
            low = j - i
            if low >= 88 * 50:                              # a BREAK
                k = j
                while k < n and samples[k] == 1:
                    k += 1
                slots, pos = [], k
                mab = k - j
                while pos < n and samples[pos] == 0:        # frames
                    mid = lambda b: pos + round((b + 0.5) * BIT)
                    if mid(10) >= n:
                        break
                    byte = sum(samples[mid(1 + b)] << b for b in range(8))
                    assert samples[mid(9)] == 1 and samples[mid(10)] == 1, "stop bits"
                    slots.append(byte)
                    pos = mid(10)
                    while pos < n and samples[pos] == 1:
                        pos += 1
                        if slots and pos - mid(10) > 50 * 1000:  # 1 ms idle: packet over
                            break
                    if pos < n and samples[pos] == 0 and pos + 1 < n:
                        # is this the next BREAK? stop at it
                        q = pos
                        while q < n and samples[q] == 0:
                            q += 1
                        if q - pos >= 88 * 50:
                            break
                out.append((low / 50, mab / 50, slots))
                i = pos
                continue
            i = j
        i += 1
    return out

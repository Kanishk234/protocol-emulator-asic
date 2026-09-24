"""Reference HDLC framing (ISO/IEC 13239, as used by X.25/PPP), written from the standard, not
from TRIPWIRE firmware or its BITSYNC model:
- a frame is its bytes sent LSB first, then the FCS-16, between flags 0x7E;
- the FCS is the reflected CRC-CCITT (poly 0x8408 reflected, init 0xFFFF), complemented and
  sent low byte first, LSB first; a good frame leaves the receiver's CRC at 0xF0B8;
- a 0 is inserted after every five consecutive 1s between the flags;
- seven or more 1s abort the frame.
"""


def fcs16(data, crc=0xFFFF):
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0x8408 if crc & 1 else crc >> 1
    return crc


def bits_of(data):
    return [(b >> i) & 1 for b in data for i in range(8)]


def stuff(bits):
    out, run = [], 0
    for b in bits:
        out.append(b)
        run = run + 1 if b else 0
        if run == 5:
            out.append(0)
            run = 0
    return out


FLAG = [0, 1, 1, 1, 1, 1, 1, 0]


def encode(frames, flags_between=2, bad_fcs=(), abort_after=None):
    """Line bits (NRZ). Frame indices in bad_fcs get a wrong FCS; abort_after = (index, nbytes)
    sends only nbytes of that frame and then an abort (seven 1s)."""
    line = [1] * 20 + FLAG * flags_between
    for i, data in enumerate(frames):
        fcs = fcs16(data) ^ 0xFFFF
        if i in bad_fcs:
            fcs ^= 0x0100
        body = bits_of(list(data) + [fcs & 0xFF, fcs >> 8])
        if abort_after and abort_after[0] == i:
            line += stuff(bits_of(data[:abort_after[1]])) + [1] * 8 + FLAG * flags_between
            continue
        line += stuff(body) + FLAG * flags_between
    return line + [1] * 20


def decode(bits):
    """[(bytes, fcs_ok)] for every frame between flags; aborted frames are dropped."""
    frames, i, n = [], 0, len(bits)
    cur, run, inside = [], 0, False
    for b in bits:
        if b:
            run += 1
            if run >= 7:
                cur, inside = [], False                 # abort / idle
            cur.append(1)
            continue
        if run == 6:                                    # 0111 1110: a flag
            body = cur[:-7] if len(cur) >= 7 else []
            if inside and body:
                data = [sum(body[8 * k + j] << j for j in range(8)) for k in range(len(body) // 8)]
                frames.append((data[:-2], fcs16(data) == 0xF0B8 and len(body) % 8 == 0))
            cur, inside, run = [], True, 0
            continue
        if run == 5:                                    # a stuffed 0: drop it
            run = 0
            continue
        run = 0
        cur.append(0)
    return frames

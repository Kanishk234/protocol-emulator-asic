"""Byte-transaction oracle for a volatile READ/FAST_READ SPI memory window.

Framing follows Winbond W25Q16JV READ 03 / FAST_READ 0B instruction descriptions:
three address bytes, then zero/eight dummy clocks. This is a deliberately small
read-only personality, not a complete model of a Winbond device or its timing.
No TRIPWIRE firmware, compiler or RTL imports belong here.
"""


def response(memory, request):
    """Expected complete MISO bytes; None means unspecified header/output.

    The small personality aliases addresses modulo the supplied window size.
    Unsupported commands have unspecified MISO and no memory side effects.
    """
    memory, request = bytes(memory), bytes(request)
    if not memory:
        raise ValueError('Memory window must be nonempty')
    result = [None] * len(request)
    if not request or request[0] not in (0x03, 0x0B):
        return result
    header = 4 if request[0] == 0x03 else 5
    if len(request) < header:
        return result
    address = int.from_bytes(request[1:4], 'big')
    for index in range(header, len(request)):
        result[index] = memory[(address + index - header) % len(memory)]
    return result


def read_request(command, address, count, *, dummy=0):
    if command not in (0x03, 0x0B) or not 0 <= address < 1 << 24 or count < 0:
        raise ValueError('Need READ/FAST_READ, a 24-bit address and nonnegative count')
    return bytes([command]) + address.to_bytes(3, 'big') + (bytes([dummy]) if command == 0x0B else b'') + bytes(count)


class FlashWireMonitor:
    """Independent sampled mode-0 read checker; reserve one setup observation."""
    def __init__(self, memory, transfers):
        self.transfers = transfers
        self.expected = [response(memory, request) for request, _ in transfers]
        self.previous_cs = 1
        self.previous_sck = 0
        self.previous_drive = None
        self.changed = 0
        self.frame = -1
        self.bits = 0
        self.setups = []

    def sample(self, clock, sck, mosi, cs, miso, enabled):
        drive = (miso, bool(enabled))
        if drive != self.previous_drive:
            self.changed = clock
        self.previous_drive = drive
        if self.previous_cs and not cs:
            self.frame += 1
            self.bits = 0
            assert self.frame < len(self.transfers), 'Extra CS assertion'
        if not cs and sck and not self.previous_sck:
            request, nbits = self.transfers[self.frame]
            limit = len(request) * 8 if nbits is None else nbits
            assert self.bits < limit, 'Extra SCK edge'
            byte, bit = divmod(self.bits, 8)
            assert mosi == (request[byte] >> (7-bit) & 1), 'MOSI framing mismatch'
            expected = self.expected[self.frame][byte]
            if expected is not None:
                assert enabled and miso == (expected >> (7-bit) & 1), 'SPI memory data mismatch'
                setup = clock - self.changed - 1
                assert setup >= 1, 'SPI memory data has insufficient sampled setup'
                self.setups.append(setup)
            self.bits += 1
        if not self.previous_cs and cs:
            request, nbits = self.transfers[self.frame]
            assert self.bits == (len(request)*8 if nbits is None else nbits), 'Truncated waveform'
        self.previous_cs, self.previous_sck = cs, sck

    def finish(self):
        assert self.frame + 1 == len(self.transfers) and self.previous_cs, 'Incomplete transfers'
        assert self.setups, 'No data-phase bit checked'
        return dict(transfers=len(self.transfers), data_bits=len(self.setups),
                    setup_lower_clocks=min(self.setups))

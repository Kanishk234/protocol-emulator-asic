"""WARP host for the Tiny Tapeout demo board (RP2040, MicroPython), D-032.

Loads a WARP bitstream file (.wbit, from tools/compile) into the chip over its host SPI port and
runs it, then talks to the user design through the host byte channel. The same file runs under
CPython (tests drive it against the chip's simulation), so it uses only what both have: no
dataclasses, enum or typing.

Pins (ARCHITECTURE.md §1): ui_in[0] HOST_CS_N, ui_in[1] HOST_SCK, ui_in[2] HOST_MOSI,
uo_out[0] HOST_MISO, uo_out[1] HOST_IRQ; ui_in[3..7] are the user design's inputs (FAB_IN0..4),
kept while the SPI pins toggle. SPI mode 0, MSB first; the shell synchronizes its pins, so every
pin level must last at least 4 project clocks (SCK <= clk/8): at the MicroPython pin-write rate
(microseconds per write) that holds for any project clock of 1 MHz or more.

On the board (copy this file and a .wbit to the RP2040's flash, e.g. with mpremote):

    import warp
    w = warp.on_demo_board(clock_hz=10_000_000)   # selects tt_um_warp, clocks and resets it
    w.load_file("uart16.wbit")                     # checked load (architecture, length, CRC)
    w.run()
    w.ch_write(0x55)                               # a byte to the user design
    w.status()                                     # dict: state, rx_valid, tx_ready, ...

Elsewhere, give Warp any object with write_ui(byte) and read_uo() -> byte (and optionally
wait(n_clocks)).
"""

import struct

try:
    import binascii
    _crc32 = binascii.crc32
except (ImportError, AttributeError):        # a MicroPython build without binascii.crc32
    _crc32 = None

SYNC_WORD = 0xFAB0FAB1
ID_MAGIC = (0x57, 0x50)                      # "WP"

# opcodes (ARCHITECTURE.md §2.3)
READ_ID, READ_STATUS = 0x01, 0x02
LOAD_BEGIN, LOAD_DATA, LOAD_END = 0x10, 0x11, 0x12
RUN, STOP, USER_RESET = 0x20, 0x21, 0x22
CH_WRITE, CH_READ, USER_STATUS = 0x30, 0x31, 0x32

STATES = ("UNCONFIGURED", "LOADING", "LOADED", "RUNNING", "ERROR")
ERRORS = {0x00: "NONE", 0x01: "BAD_COMMAND", 0x10: "WRONG_ARCH", 0x11: "LENGTH",
          0x12: "CRC", 0x13: "FORMAT"}

CS_N, SCK, MOSI = 0, 1, 2
HALF, CS_SETUP, CS_IDLE = 4, 8, 4            # project clocks (used only by pins with wait())


class WarpError(Exception):
    pass


def crc32(data):
    """CRC-32 (IEEE 802.3, as zlib) of a bytes-like object."""
    if _crc32 is not None:
        return _crc32(data) & 0xFFFFFFFF
    crc = 0xFFFFFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ (0xEDB88320 if crc & 1 else 0)
    return crc ^ 0xFFFFFFFF


def parse_wbit(data):
    """(arch_version, words) of a .wbit file (tools/compile/bitfile.py), with its checks."""
    if len(data) < 16 or data[:4] != b"WBIT":
        raise WarpError("not a WARP bitstream file")
    arch, _, n, crc = struct.unpack(">HHII", data[4:16])
    body = data[16:]
    if len(body) != 4 * n:
        raise WarpError("truncated bitstream file")
    if crc32(body) != crc:
        raise WarpError("CRC mismatch in bitstream file")
    words = [struct.unpack(">I", body[4 * i:4 * i + 4])[0] for i in range(n)]
    if not words or words[0] != SYNC_WORD:
        raise WarpError("first word is not the sync word")
    return arch, words


def decode_status(b):
    return {"state": STATES[(b >> 5) & 7] if (b >> 5) & 7 < len(STATES) else (b >> 5) & 7,
            "rx_valid": bool(b & 0x10), "tx_ready": bool(b & 0x08), "ch_overflow": bool(b & 0x04),
            "user_attention": bool(b & 0x02), "error_pending": bool(b & 0x01)}


def _be(v, n):
    return [(v >> (8 * (n - 1 - i))) & 0xFF for i in range(n)]


def load_transactions(words, arch, chunk=64):
    """MOSI bytes of every transaction of a load (ARCHITECTURE.md §3)."""
    txs = [[LOAD_BEGIN] + _be(arch, 2) + _be(len(words), 2)]
    for i in range(0, len(words), chunk):
        tx = [LOAD_DATA]
        for w in words[i:i + chunk]:
            tx += _be(w, 4)
        txs.append(tx)
    body = bytes([b for w in words for b in _be(w, 4)])
    txs.append([LOAD_END] + _be(crc32(body), 4))
    return txs


class Warp:
    def __init__(self, pins):
        self.pins = pins
        self.fab_in = 0
        self._spi = 1 << CS_N
        self._drive()

    # ---- pins
    def _drive(self):
        self.pins.write_ui((self.fab_in & 0x1F) << 3 | self._spi)

    def _set(self, cs_n, sck, mosi, clocks):
        self._spi = cs_n << CS_N | sck << SCK | mosi << MOSI
        self._drive()
        wait = getattr(self.pins, "wait", None)
        if wait:
            wait(clocks)

    def set_fab_in(self, value):
        """Drive the user design's inputs FAB_IN0..4 (ui_in[3..7])."""
        self.fab_in = value & 0x1F
        self._drive()

    def xfer(self, mosi_bytes):
        """One transaction (CS low ... CS high); returns the MISO bytes."""
        self._set(0, 0, 0, CS_SETUP)
        miso = []
        for byte in mosi_bytes:
            r = 0
            for i in range(7, -1, -1):
                bit = (byte >> i) & 1
                self._set(0, 0, bit, HALF)
                r = (r << 1) | (self.pins.read_uo() & 1)      # sampled before the rising edge
                self._set(0, 1, bit, HALF)
            miso.append(r)
        self._set(0, 0, 0, HALF)
        self._set(1, 0, 0, CS_IDLE)
        return miso

    # ---- commands
    def read_id(self):
        """Architecture version the chip was built for; WarpError if it is not a WARP chip."""
        m = self.xfer([READ_ID, 0, 0, 0, 0])
        if (m[1], m[2]) != ID_MAGIC:
            raise WarpError("READ_ID magic mismatch: not a WARP chip, or no clock/reset")
        return m[3] << 8 | m[4]

    def status(self):
        return decode_status(self.xfer([READ_ID])[0])

    def read_status(self):
        """(status dict, error name)."""
        m = self.xfer([READ_STATUS, 0, 0])
        return decode_status(m[1]), ERRORS.get(m[2], m[2])

    def load(self, arch, words, chunk=64):
        """Checked load: refuses a bitstream for another architecture before sending anything;
        raises WarpError unless the chip ends in LOADED."""
        chip = self.read_id()
        if arch != chip:
            raise WarpError("bitstream is for architecture 0x%04X, the chip is 0x%04X" % (arch, chip))
        if self.status()["state"] == "RUNNING":
            raise WarpError("the chip is RUNNING: stop() before loading (ARCHITECTURE §3)")
        for tx in load_transactions(words, arch, chunk):
            self.xfer(tx)
        st, err = self.read_status()
        if st["state"] != "LOADED":
            raise WarpError("load failed: state %s, error %s" % (st["state"], err))

    def load_file(self, path, chunk=64):
        with open(path, "rb") as f:
            arch, words = parse_wbit(f.read())
        self.load(arch, words, chunk)

    def _command(self, op, want):
        self.xfer([op])
        st, err = self.read_status()
        if want and st["state"] != want:
            raise WarpError("state %s after 0x%02X (error %s)" % (st["state"], op, err))

    def run(self):
        self._command(RUN, "RUNNING")

    def stop(self):
        self._command(STOP, None)

    def user_reset(self):
        self._command(USER_RESET, None)

    def ch_write(self, byte, last=False, tries=1000):
        """A byte to the user design (h_wdata); waits until the channel has room."""
        for _ in range(tries):
            if self.status()["tx_ready"]:
                self.xfer([CH_WRITE, 1 if last else 0, byte & 0xFF])
                return
        raise WarpError("host channel full")

    def ch_read(self, tries=1000):
        """The next byte from the user design (h_rdata), or None if none arrived."""
        for _ in range(tries):
            if self.status()["rx_valid"]:
                return self.xfer([CH_READ, 0])[1]
        return None

    def user_status(self):
        """The user design's h_status byte."""
        return self.xfer([USER_STATUS, 0])[1]


class _DemoBoardPins:
    def __init__(self, platform):
        self.write_ui = platform.write_ui_in_byte
        self.read_uo = platform.read_uo_out_byte


def on_demo_board(clock_hz=10_000_000, project="tt_um_warp"):
    """Select the WARP project on a Tiny Tapeout demo board, clock it, reset it (ttboard SDK)."""
    from ttboard.demoboard import DemoBoard
    import ttboard.util.platform as platform
    tt = DemoBoard.get()
    getattr(tt.shuttle, project).enable()
    tt.clock_project_PWM(clock_hz)
    tt.reset_project(True)
    w = Warp(_DemoBoardPins(platform))
    tt.reset_project(False)
    return w

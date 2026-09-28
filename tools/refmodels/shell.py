"""WARP shell: independent reference model of the host interface, loader and run control.

Written from docs/design/ARCHITECTURE.md §2-§4 and §7.3 (and D-021, BUGS #12 as cited there),
not from src/wp_shell.v. Transaction level: one call per SPI transaction (CS_N low to high).

  - Every transaction's first byte is the opcode; while it shifts in, the chip shifts out STATUS.
    One command per transaction; bytes after a command's payload/response are ignored.
  - STATUS = {STATE[2:0], rx_valid, tx_ready, ch_overflow, user_attention, error_pending}.
    tx_ready means a CH_WRITE would be accepted now, so it is 0 unless RUNNING (§2.3–2.4).
  - A command not allowed in the current state (or an unknown opcode) is ignored and sets
    ERROR_CODE 0x01 only if ERROR_CODE is 0. LOAD_BEGIN is allowed in every state but RUNNING.
  - A load: LOAD_BEGIN checks ARCH_VERSION (wrong: ERROR, code 0x10). LOAD_DATA words are
    counted and CRC'd; the first word must be the sync word 0xFAB0FAB1 (else forwarding stops),
    words beyond LENGTH are not forwarded. LOAD_END checks, in order: sync (also 0x13 for no
    words), LENGTH (0x11), CRC-32 (0x12, IEEE 802.3 over the words' big-endian bytes). A load
    error always replaces ERROR_CODE. Success: LOADED.
  - RUN (LOADED -> RUNNING), STOP (RUNNING -> LOADED), USER_RESET (RUNNING, pulses user reset).
  - Host channels: a 2-entry FIFO each way, emptied whenever STATE != RUNNING. CH_WRITE while
    the host->design FIFO is full drops the byte and sets the sticky ch_overflow. CH_READ pops.
  - READ_STATUS returns STATUS then ERROR_CODE; after the ERROR_CODE byte is sent, ERROR_CODE
    and ch_overflow clear.
  - A transaction that ends early discards the partial byte and command; LOAD_DATA keeps the
    whole words already received.
  - HOST_IRQ = rx_valid | user_attention | (STATE == ERROR).

The design side of the host channel is supplied by the caller (`fabric`): an object with
`settle(model)` that moves bytes between the FIFOs and the design once the shell is idle, and
`user_reset()`; plus attributes `status` and `attention` (what the design drives).
"""

import binascii

READ_ID, READ_STATUS = 0x01, 0x02
LOAD_BEGIN, LOAD_DATA, LOAD_END = 0x10, 0x11, 0x12
RUN, STOP, USER_RESET = 0x20, 0x21, 0x22
CH_WRITE, CH_READ, USER_STATUS = 0x30, 0x31, 0x32
OPCODES = (READ_ID, READ_STATUS, LOAD_BEGIN, LOAD_DATA, LOAD_END, RUN, STOP, USER_RESET,
           CH_WRITE, CH_READ, USER_STATUS)
NAMES = {READ_ID: "READ_ID", READ_STATUS: "READ_STATUS", LOAD_BEGIN: "LOAD_BEGIN",
         LOAD_DATA: "LOAD_DATA", LOAD_END: "LOAD_END", RUN: "RUN", STOP: "STOP",
         USER_RESET: "USER_RESET", CH_WRITE: "CH_WRITE", CH_READ: "CH_READ",
         USER_STATUS: "USER_STATUS"}

UNCONFIGURED, LOADING, LOADED, RUNNING, ERROR = range(5)
STATE_NAMES = ("UNCONFIGURED", "LOADING", "LOADED", "RUNNING", "ERROR")

E_NONE, E_BAD_CMD, E_ARCH, E_LENGTH, E_CRC, E_SYNC = 0x00, 0x01, 0x10, 0x11, 0x12, 0x13
SYNC_WORD = 0xFAB0FAB1
FIFO_DEPTH = 2

ALLOWED = {
    READ_ID: set(range(5)), READ_STATUS: set(range(5)),
    LOAD_BEGIN: {UNCONFIGURED, LOADING, LOADED, ERROR},
    LOAD_DATA: {LOADING}, LOAD_END: {LOADING}, RUN: {LOADED},
    STOP: {RUNNING}, USER_RESET: {RUNNING},
    CH_WRITE: {RUNNING}, CH_READ: {RUNNING}, USER_STATUS: {RUNNING},
}
# payload bytes host -> chip (LOAD_DATA: any multiple of 4) and response bytes chip -> host
PAYLOAD = {LOAD_BEGIN: 4, LOAD_END: 4, CH_WRITE: 2}
RESPONSE = {READ_ID: 4, READ_STATUS: 2, CH_READ: 1, USER_STATUS: 1}


class NoFabric:
    """A design that never accepts or produces channel bytes."""
    status = 0
    attention = 0

    def settle(self, model):
        pass

    def user_reset(self):
        pass


class ShellModel:
    def __init__(self, arch_version, fabric=None):
        self.arch = arch_version
        self.fabric = fabric or NoFabric()
        self.forwarded = []           # every configuration word forwarded, in order
        self.reset()

    def reset(self):
        self.state = UNCONFIGURED
        self.code = E_NONE
        self.overflow = 0
        self.tx = []                  # host -> design FIFO: (data, last)
        self.rx = []                  # design -> host FIFO: data
        self._load_reset(0)
        self.fabric.user_reset()

    def _load_reset(self, length):
        self.length = length
        self.words = 0
        self.crc_bytes = bytearray()
        self.sync_ok = None           # None: no word yet

    # ---- observable state -------------------------------------------------------------
    @property
    def attention(self):
        return int(bool(self.fabric.attention)) if self.state == RUNNING else 0

    def status(self):
        return ((self.state << 5) | (int(bool(self.rx)) << 4)
                | (int(len(self.tx) < FIFO_DEPTH and self.state == RUNNING) << 3)
                | (self.overflow << 2) | (self.attention << 1) | int(self.code != E_NONE))

    def irq(self):
        return int(bool(self.rx) or bool(self.attention) or self.state == ERROR)

    # ---- helpers ------------------------------------------------------------------------
    def _load_error(self, code):
        self.state = ERROR
        self.code = code

    def _bad_command(self):
        if self.code == E_NONE:
            self.code = E_BAD_CMD

    def _leave_running(self):
        self.tx.clear()
        self.rx.clear()
        self.fabric.user_reset()

    def _word(self, w):
        if self.sync_ok is None:
            self.sync_ok = (w == SYNC_WORD)
        self.crc_bytes += w.to_bytes(4, "big")
        if self.sync_ok and self.words < self.length:
            self.forwarded.append(w)
        self.words += 1

    # ---- one SPI transaction --------------------------------------------------------------
    def transaction(self, mosi, nbits=None):
        """`mosi`: the bytes the host sends; `nbits`: bits clocked before CS_N rose (default: all).
        Returns the expected MISO bytes (None where the chip's output is unspecified)."""
        if nbits is None:
            nbits = 8 * len(mosi)
        nbytes = nbits // 8                          # whole bytes the chip received
        miso = [None] * len(mosi)
        if len(mosi) >= 1:
            miso[0] = self.status()
        if nbytes == 0:
            return miso                              # partial opcode: discarded
        op = mosi[0]
        body = mosi[1:nbytes]
        allowed = op in ALLOWED and self.state in ALLOWED[op]
        need = PAYLOAD.get(op, 0)

        if not allowed:
            self._bad_command()
        elif op == READ_ID:
            resp = [0x57, 0x50, self.arch >> 8, self.arch & 0xFF]
            for i in range(min(4, len(mosi) - 1)):
                miso[1 + i] = resp[i]
        elif op == READ_STATUS:
            if len(mosi) >= 2:
                miso[1] = self.status()
            if len(mosi) >= 3:
                miso[2] = self.code
            if nbytes >= 3:                          # the ERROR_CODE byte was sent
                self.code = E_NONE
                self.overflow = 0
        elif op == LOAD_BEGIN:
            if len(body) >= need:
                ver = (body[0] << 8) | body[1]
                length = (body[2] << 8) | body[3]
                if self.state == RUNNING:            # not reachable (not allowed); kept for clarity
                    self._leave_running()
                if ver != self.arch:
                    self._load_error(E_ARCH)
                    self._load_reset(0)
                else:
                    self.state = LOADING
                    self._load_reset(length)
        elif op == LOAD_DATA:
            for i in range(len(body) // 4):
                self._word(int.from_bytes(bytes(body[4 * i:4 * i + 4]), "big"))
        elif op == LOAD_END:
            if len(body) >= need:
                crc = int.from_bytes(bytes(body[:4]), "big")
                if not self.sync_ok:
                    self._load_error(E_SYNC)
                elif self.words != self.length:
                    self._load_error(E_LENGTH)
                elif crc != (binascii.crc32(bytes(self.crc_bytes)) & 0xFFFFFFFF):
                    self._load_error(E_CRC)
                else:
                    self.state = LOADED
        elif op == RUN:
            self.state = RUNNING
        elif op == STOP:
            self.state = LOADED
            self._leave_running()
        elif op == USER_RESET:
            self.fabric.user_reset()
        elif op == CH_WRITE:
            if len(body) >= need:
                if len(self.tx) >= FIFO_DEPTH:
                    self.overflow = 1
                else:
                    self.tx.append((body[1], body[0] & 1))
        elif op == CH_READ:
            if len(mosi) >= 2 and self.rx:
                miso[1] = self.rx[0]
            if nbytes >= 2 and self.rx:
                self.rx.pop(0)
        elif op == USER_STATUS:
            if len(mosi) >= 2:
                miso[1] = self.fabric.status & 0xFF
        if self.state == RUNNING:
            self.fabric.settle(self)
        return miso

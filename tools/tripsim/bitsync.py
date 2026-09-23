"""BITSYNC pin-unit mode (DECISIONS D-021; ARCHITECTURE.md §14 P20-P26).

One bit clock shared by TX and RX, recovered from the line:
- hard sync on the first recessive-to-dominant edge at bus idle (or at our own frame start);
- resync on later edges, limited to SJW clocks, at most once per bit, and not on edges we
  cause while driving the dominant level;
- a sample point at SAMPLEOFS of the bit; bus idle after IDLE_BITS recessive samples.
Line coding between the bit clock and the words:
- bit stuffing (after STUFF_N equal bits the next is the complement; STUFF_LVL limits it to
  runs of one level), removed on RX and inserted on TX;
- a CRC (any polynomial up to 16 bits) over the destuffed RX bits of the frame, appended to
  TX on request and checked against CRC_RES when the frame length (FRAME) is reached;
- readback: compare each bit we drive with the sampled line, abort or report.
Nothing here is specific to one protocol; CAN is one configuration of it.

Time and edges follow pinunit.py: a TX level set in clock t is on the pad from clock t+1.
"""

from collections import deque

from . import isa

# TX status EVENTs: data[15] = 1, [14] sampled level, [13:12] kind, [11:1] line bit, [0] = started
EV_ABORT, EV_STARTED, EV_REPORT = 0x8000, 0x9001, 0xA000
ERR_CRC, ERR_STUFF = 0, 1   # ERR data[15:12]


class BitSync:
    def __init__(self, unit):
        self.u = unit
        c = unit.cfg
        self.rec = c.idle                       # recessive level
        self.P = c.period_q8
        self.SP = round(c.sampleofs * self.P)
        self.SJW = round(c.sjw * 256)
        self.t = 0                              # start of the current bit (1/256 clock)
        self.sampled = self.resynced = False
        self.idle_cnt = 0
        self.prev = None
        # RX frame
        self.in_frame = False
        self.bitno = 0                          # line bits sampled since the frame start
        self.rx_on = False                      # word framing active
        self.frame_bits = 0                     # destuffed bits of the frame so far
        self.frame_n = self.frame_n_next = 0
        self.rx_stuff = False
        self.run_lvl, self.run_n = None, 0
        self.post_check = False
        self.crc = 0
        self.bits = []
        self.rx_len = c.rx_nbits or c.nbits
        # TX
        self.q = deque()                        # ("b", v) | ("line", arg) | ("sync",)
        self.newframe = False                   # a SYNC is at the head: start a frame at idle
        self.tx_bit = None                      # level we drive in this bit (None: released)
        self.tx_rb = 0                          # readback mode of that bit
        self.rb, self.tx_stuff = 0, False
        self.tx_run_lvl, self.tx_run_n = None, 0
        self.discard = False
        self.wait_sp = False
        self.own = False                        # this unit transmits the frame in progress
        self.override = None                    # one-bit override: (level, armed)
        self.out = deque()

    # ------------------------------------------------------------ helpers
    def _emit(self, tag, data):
        if len(self.out) < 2:                   # 2-token skid buffer in front of the producer
            self.out.append((tag, data))
        else:
            self.u.flags["OVERRUN"] = 1
            self.u.stats["overruns"] += 1

    def _word(self, bits):
        n = len(bits)
        if self.u.cfg.order == "msb":
            return sum(b << (n - 1 - i) for i, b in enumerate(bits))
        return sum(b << i for i, b in enumerate(bits))

    def _drive(self, now, v):
        self.u._tx_apply.append((now, "level", self.rec if v is None else v))

    def _start_frame(self, now_q8):
        c = self.u.cfg
        self.t = now_q8
        self.sampled = self.resynced = False
        self.in_frame, self.rx_on = True, True
        self.bitno = self.frame_bits = 0
        self.frame_n, self.frame_n_next = self.frame_n_next, 0
        self.rx_stuff = c.stuff_n > 0
        self.run_lvl, self.run_n = None, 0
        self.post_check = False
        self.crc = c.crc_init
        self.bits = []
        self.tx_run_lvl, self.tx_run_n = None, 0

    # ------------------------------------------------------------ RX / timing
    def step(self, now, s):
        """Called once per clock with the synchronised sense level s."""
        c = self.u.cfg
        now_q8 = now << 8
        if (self.newframe and not self.in_frame and self.idle_cnt >= c.idle_bits
                and self.sampled and any(k[0] == "b" for k in self.q)):
            # our frame starts at the next bit boundary after bus idle (§14 P21)
            if now_q8 >= self.t + self.P:
                self.newframe = False
                self._start_frame(now_q8)
                self.own = True
                self._emit(isa.TAG_EVENT, EV_STARTED)
                self._tx_bit_start(now)
        edge = self.prev is not None and s != self.prev
        if edge and (s != self.rec or c.resync == "both"):
            if not self.in_frame and self.idle_cnt >= c.idle_bits and s != self.rec:
                self._start_frame(now_q8)                              # hard sync
                self.own = False
                first = next((k for k in self.q if k[0] == "b"), None)
                if self.newframe and first is not None and first[1] != self.rec:
                    self.newframe = False       # join: our dominant first bit is this bit (P21)
                    self.own = True
                    self._emit(isa.TAG_EVENT, EV_STARTED)
                self._tx_bit_start(now)
            elif (self.SJW and not self.resynced
                  and not (self.tx_bit is not None and self.tx_bit != self.rec)):
                e = now_q8 - self.t
                if e <= self.SP:                                       # late edge: stretch
                    self.t += min(e, self.SJW)
                else:                                                  # early edge: shorten
                    self.t -= min(self.t + self.P - now_q8, self.SJW)
                self.resynced = True
        if now_q8 >= self.t + self.P:
            self.t += self.P
            self.sampled = self.resynced = False
            self._tx_bit_start(now)
        if not self.sampled and now_q8 >= self.t + self.SP:
            self.sampled = True
            self._sample(s)
            self.wait_sp = False
        self.prev = s
        prod = self.u.rx_prod
        if self.out and prod.free():
            prod.load(*self.out.popleft())
            self.u.stats["rx_tokens"] += 1

    def _sample(self, s):
        stuff = self._sample_bit(s)
        if self.override is not None and not stuff:
            self.override = (self.override[0], True)             # applies at the next bit start

    def _sample_bit(self, s):
        """Process one sample; True if it was a stuff bit (removed)."""
        c = self.u.cfg
        self.idle_cnt = self.idle_cnt + 1 if s == self.rec else 0
        if self.tx_bit is not None and self.tx_rb:
            if self.tx_rb == 2:
                self._emit(isa.TAG_EVENT, EV_REPORT | s << 14 | (self.bitno & 0x7FF) << 1)
            elif s != self.tx_bit:
                self._emit(isa.TAG_EVENT, EV_ABORT | s << 14 | (self.bitno & 0x7FF) << 1)
                self._abort()
        if not self.in_frame:
            return False
        self.bitno += 1
        if self.rx_on or self.post_check:
            if self.rx_stuff and self._stuff_due():
                if s == self.run_lvl:
                    self._emit(isa.TAG_ERR, ERR_STUFF << 12 | (self.bitno & 0xFFF))
                    self.rx_on = self.post_check = False
                    return False
                self.run_lvl, self.run_n = s, 1 if c.stuff_lvl in (None, s) else 0
                if self.post_check:
                    self.post_check = self.rx_stuff = False
                return True                                            # stuff bit removed
            if self.post_check:
                self.post_check = self.rx_stuff = False
                return False
            self._run(s)
            self._frame_bit(s)
        if self.idle_cnt >= c.idle_bits and self.tx_bit is None:
            self.in_frame = self.rx_on = False
        return False

    def _stuff_due(self):
        return self.run_n >= self.u.cfg.stuff_n

    def _run(self, s):
        lvl = self.u.cfg.stuff_lvl
        if lvl is None:
            self.run_n = self.run_n + 1 if s == self.run_lvl else 1
        else:
            self.run_n = self.run_n + 1 if s == lvl else 0
        self.run_lvl = s

    def _frame_bit(self, s):
        c = self.u.cfg
        self.frame_bits += 1
        if c.crc_width:
            msb = (self.crc >> (c.crc_width - 1)) & 1
            self.crc = (self.crc << 1) & ((1 << c.crc_width) - 1)
            if msb ^ s:
                self.crc ^= c.crc_poly
        self.bits.append(s)
        if self.frame_n and self.frame_bits == self.frame_n:          # §14 P24
            ok = not c.crc_width or self.crc == c.crc_res
            w = self._word(self.bits) & 0xFFF
            self._emit(isa.TAG_EVENT if ok else isa.TAG_ERR, w if ok else ERR_CRC << 12 | w)
            self.bits, self.rx_on = [], False
            self.post_check = self.rx_stuff
        elif len(self.bits) == self.rx_len:
            self._emit(isa.TAG_DATA, self._word(self.bits))
            self.bits = []

    # ------------------------------------------------------------ TX
    def _abort(self):
        self.own = False
        self.q.clear()
        self.tx_bit, self.tx_rb = None, 0
        self.rb, self.tx_stuff = 0, False
        self.newframe = False
        self.discard = True

    def _tx_bit_start(self, now):
        c = self.u.cfg
        if self.override is not None and self.override[1]:
            v, self.override = self.override[0], None
            if not (self.own and self.in_frame):                 # never over our own frame
                self.tx_bit, self.tx_rb = v, 0
                self._drive(now, v)
                return
        while self.q and self.q[0][0] != "b":
            item = self.q[0]
            if item[0] == "sync":
                if not self.in_frame or self.newframe:
                    self.q.popleft()
                    self.newframe = True
                break
            self.q.popleft()
            arg = item[1]
            self.rb, self.tx_stuff = arg & 3, bool(arg & 4)
            if arg & 8 and c.crc_width:
                for i in reversed(range(c.crc_width)):
                    self.q.appendleft(("b", (self.crc >> (c.crc_width - 1 - i)) & 1))
        if self.newframe and not self.in_frame:
            self.tx_bit = None                  # waiting for bus idle
            self._drive(now, None)
            return
        if self.tx_stuff and c.stuff_n and self.tx_run_n >= c.stuff_n and self.q and self.q[0][0] == "b":
            v = 1 - self.tx_run_lvl                                    # stuff bit
        elif self.q and self.q[0][0] == "b":
            v = self.q.popleft()[1]
        else:
            self.tx_bit, self.tx_rb = None, 0
            self._drive(now, None)
            return
        if self.tx_stuff:
            if c.stuff_lvl is None:
                self.tx_run_n = self.tx_run_n + 1 if v == self.tx_run_lvl else 1
            else:
                self.tx_run_n = self.tx_run_n + 1 if v == c.stuff_lvl else 0
            self.tx_run_lvl = v
        self.tx_bit, self.tx_rb = v, self.rb
        self._drive(now, v)

    def accept(self, now, port, cmds):
        """TX half: take one token if it may be taken now (§14 P25)."""
        if port is None or not port.avail():
            return
        tag, data = port.head()
        c = self.u.cfg
        op, arg = data >> 12, data & 0xFFF
        rx_cmd = tag == isa.TAG_CTRL and (op == cmds["FRAME"] or (op == cmds["SETN"] and arg & 0x20)
                                          or (op == cmds["LINE"] and arg & 0x10))
        if not rx_cmd:
            if self.wait_sp or any(k[0] == "b" for k in self.q):
                return
        port.take()
        self.u.stats["tx_tokens"] += 1
        if rx_cmd:
            if op == cmds["LINE"]:                                  # one-bit override (§14 P26)
                self.override = ((arg >> 5) & 1, False)
            elif op == cmds["FRAME"]:
                n = arg & 0x7FF
                if arg & 0x800:                 # for the next frame
                    self.frame_n_next = n
                elif self.in_frame and self.rx_on and self.frame_bits < n:
                    self.frame_n = n            # for the frame in progress
                else:
                    self.u.flags["LATE"] = 1    # no frame, or already past n bits
            else:
                self.rx_len = (arg & 0x1F) or 16
                self.bits = []
            return
        if tag == isa.TAG_CTRL and op == cmds["SYNC"]:
            self.discard = False
            self.q.append(("sync",))
        elif tag == isa.TAG_CTRL and op == cmds["WAIT"] and arg & 2:
            self.discard = False                # a WAIT is also a synchronisation point
            self.wait_sp = True
        elif self.discard:
            pass                                # after a readback abort, until SYNC or WAIT
        elif tag == isa.TAG_CTRL and op == cmds["LINE"]:
            self.q.append(("line", arg))
        elif tag == isa.TAG_DATA:
            n = c.nbits
            if c.tx_lentok:
                n, data = (data >> 12) + 1, data & 0x0FFF
            bits = [(data >> i) & 1 for i in range(n)] if c.order == "lsb" else \
                   [(data >> (n - 1 - i)) & 1 for i in range(n)]
            self.q.extend(("b", v) for v in bits)
        else:
            self.u.stats["bad_tokens"] += 1

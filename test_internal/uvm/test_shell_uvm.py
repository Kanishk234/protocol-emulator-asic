"""pyuvm (UVM in Python) environment for the WARP shell (`src/wp_shell.v`).

Constrained-random host transactions over the real SPI pins, checked against the independent
reference model `tools/refmodels/shell.py` (written from ARCHITECTURE §2-§4), with functional
coverage of every command in every state, every error code, the STATUS flags and aborted
transactions. White-box (the shell alone, the fabric side played by a loopback agent), so it
lives in test_internal/.

  env
  ├── host_agent: sequencer → driver (bit-bangs SPI mode 0, drives rst_n)
  │               spi_monitor (passive, decodes CS_N/SCK/MOSI/MISO/IRQ) ──┐
  ├── cfg_monitor (configuration words: cfg_strobe/cfg_word) ─────────────┤
  ├── fabric_agent (loopback user design: echoes host bytes back) ────────┤
  ├── scoreboard (reference model; compares every response byte, the     ◄┘
  │               forwarded configuration words, the design-side bytes, HOST_IRQ)
  └── coverage (command × state, error codes, STATUS flags, aborts)

Seed: cocotb's RANDOM_SEED (printed at start; rerun with RANDOM_SEED=<n>). Length: UVM_ITEMS.
"""

import binascii
import json
import os
import random
import sys
from pathlib import Path

import cocotb
import pyuvm
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge
from pyuvm import (ConfigDB, uvm_analysis_port, uvm_component, uvm_driver, uvm_env,
                   uvm_sequence, uvm_sequence_item, uvm_sequencer, uvm_subscriber,
                   uvm_test, uvm_tlm_analysis_fifo)

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from refmodels import shell as sm  # noqa: E402

ARCH = int(os.environ.get("WARP_ARCH_VERSION", "3"), 0)
HALF = 4                  # SCK half period in clk (SCK = clk/8, the fastest allowed)
LEAD = 10                 # CS_N falling to the first SCK rising edge (>= 8 clk)
GAP = 40                  # CS_N high between transactions (>= 4 clk; lets the shell settle)
SETTLE = 20               # monitors publish a transaction this long after CS_N rises
UNKNOWN_OPS = (0x00, 0x03, 0x13, 0x23, 0x33, 0x7F, 0xFF)


# ---- transactions ---------------------------------------------------------------------------
class ShellItem(uvm_sequence_item):
    """kind 'spi' (mosi bytes, nbits clocked before CS_N rises), 'reset', or 'fabric'
    (what the user design drives on h_status / h_attention)."""

    def __init__(self, name="item", kind="spi", mosi=(), nbits=None, status=0, attention=0):
        super().__init__(name)
        self.kind, self.mosi, self.nbits = kind, list(mosi), nbits
        self.status, self.attention = status, attention
        self.miso = []

    def __str__(self):
        if self.kind != "spi":
            return f"{self.kind}"
        op = sm.NAMES.get(self.mosi[0], f"0x{self.mosi[0]:02x}") if self.mosi else "-"
        return f"{op} {bytes(self.mosi[1:9]).hex()} nbits={self.nbits}"


def val(sig, default=0):
    """A signal's integer value;  while it is X/Z (before reset)."""
    v = sig.value
    return int(v) if v.is_resolvable else default


class SpiTxn:
    def __init__(self, mosi, miso, nbits, irq):
        self.mosi, self.miso, self.nbits, self.irq = mosi, miso, nbits, irq


# ---- sequences ------------------------------------------------------------------------------
class BaseSeq(uvm_sequence):
    async def send(self, mosi, nbits=None):
        it = ShellItem("spi", mosi=mosi, nbits=nbits)
        await self.start_item(it)
        await self.finish_item(it)
        return it

    async def reset(self):
        it = ShellItem("reset", kind="reset")
        await self.start_item(it)
        await self.finish_item(it)

    async def fabric(self, status, attention):
        it = ShellItem("fabric", kind="fabric", status=status, attention=attention)
        await self.start_item(it)
        await self.finish_item(it)


def payload_for(op, rng):
    if op == sm.LOAD_BEGIN:
        ver = ARCH if rng.random() < 0.8 else rng.choice([ARCH ^ 1, 0, 0xFFFF])
        n = rng.randint(0, 6)
        return [ver >> 8, ver & 0xFF, 0, n]
    if op == sm.LOAD_DATA:
        return [rng.randrange(256) for _ in range(4 * rng.randint(0, 2))]
    if op in (sm.LOAD_END, sm.CH_WRITE):
        return [rng.randrange(256) for _ in range(sm.PAYLOAD[op])]
    return [0] * sm.RESPONSE.get(op, rng.randint(0, 1))


class RandomCmdSeq(BaseSeq):
    """Any opcode (including unknown ones) with a plausible payload, in whatever state."""

    def __init__(self, name, rng, n):
        super().__init__(name)
        self.rng, self.n = rng, n

    async def body(self):
        for _ in range(self.n):
            op = self.rng.choice(sm.OPCODES + UNKNOWN_OPS)
            await self.send([op] + payload_for(op, self.rng))


class LoadSeq(BaseSeq):
    """A load: correct, or with one injected fault. LOAD_DATA chunks are 1-3 words; some chunks
    are aborted mid-word and the rest resent (whole words are kept, §2.2)."""

    FAULTS = (None, None, None, "arch", "short", "long", "crc", "sync", "empty", "abort_end",
              "abandon")

    def __init__(self, name, rng, fault="random"):
        super().__init__(name)
        self.rng = rng
        self.fault = rng.choice(self.FAULTS) if fault == "random" else fault

    async def body(self):
        r, f = self.rng, self.fault
        n = 0 if f == "empty" else r.randint(1, 10)
        words = [sm.SYNC_WORD] + [r.getrandbits(32) for _ in range(n - 1)] if n else []
        if f == "sync":
            words[0] ^= 1 << r.randrange(32)
        length = n + (1 if f == "short" else -1 if f == "long" and n else 0)
        ver = ARCH ^ (1 << r.randrange(16)) if f == "arch" else ARCH
        await self.send([sm.LOAD_BEGIN, ver >> 8, ver & 0xFF, length >> 8, length & 0xFF])
        data = b"".join(w.to_bytes(4, "big") for w in words)
        i = 0
        while i < len(words):
            k = min(r.randint(1, 3), len(words) - i)
            chunk = list(data[4 * i:4 * (i + k)])
            if r.random() < 0.15:                   # abort inside word j, then resend from j
                j = r.randrange(k)
                cut = 8 + 32 * j + r.randint(1, 31)
                await self.send([sm.LOAD_DATA] + chunk, nbits=cut)
                i += j
                continue
            await self.send([sm.LOAD_DATA] + chunk)
            i += k
        if f == "abandon":                          # no LOAD_END: stays LOADING
            return
        crc = binascii.crc32(data) & 0xFFFFFFFF
        if f == "crc":
            crc ^= 1 << r.randrange(32)
        end = [sm.LOAD_END] + list(crc.to_bytes(4, "big"))
        if f == "abort_end":                        # aborted LOAD_END is discarded; resend it
            await self.send(end, nbits=8 + r.randint(0, 31))
        await self.send(end)


class RunTrafficSeq(BaseSeq):
    """While RUNNING: channel traffic in both directions, overflow, status, attention."""

    def __init__(self, name, rng, n):
        super().__init__(name)
        self.rng, self.n = rng, n

    async def body(self):
        r = self.rng
        await self.send([sm.RUN])
        for _ in range(self.n):
            x = r.random()
            if x < 0.35:
                burst = r.randint(1, 7)             # more than the loop holds: overflow
                for _ in range(burst):
                    await self.send([sm.CH_WRITE, r.randrange(2), r.randrange(256)])
            elif x < 0.6:
                await self.send([sm.CH_READ, 0])
            elif x < 0.7:
                await self.send([sm.READ_STATUS, 0, 0])
            elif x < 0.78:
                await self.fabric(r.randrange(256), r.randrange(2))
                await self.send([sm.USER_STATUS, 0])
            elif x < 0.83:
                await self.send([sm.USER_RESET])
            elif x < 0.86:                          # aborted CH_WRITE (mid FLAGS or DATA)
                await self.send([sm.CH_WRITE, 1, r.randrange(256)], nbits=r.randint(9, 23))
            elif x < 0.95:
                op = r.choice(sm.OPCODES + UNKNOWN_OPS)
                await self.send([op] + payload_for(op, r))
            else:
                await self.send([sm.READ_ID, 0, 0, 0, 0])
        if r.random() < 0.7:
            await self.send([sm.STOP])


class ClosureSeq(BaseSeq):
    """Coverage-driven closure: for each command × state bin the random sessions missed, drive
    the shell into that state (reset, then the load steps) and send the command."""

    def __init__(self, name, rng, cov):
        super().__init__(name)
        self.rng, self.cov = rng, cov

    async def goto(self, state):
        await self.reset()
        if state == sm.UNCONFIGURED:
            return
        if state == sm.ERROR:
            ver = ARCH ^ 0x8000
            await self.send([sm.LOAD_BEGIN, ver >> 8, ver & 0xFF, 0, 1])
            return
        await self.send([sm.LOAD_BEGIN, ARCH >> 8, ARCH & 0xFF, 0, 1])
        if state == sm.LOADING:
            return
        await self.send([sm.LOAD_DATA] + list(sm.SYNC_WORD.to_bytes(4, "big")))
        crc = binascii.crc32(sm.SYNC_WORD.to_bytes(4, "big")) & 0xFFFFFFFF
        await self.send([sm.LOAD_END] + list(crc.to_bytes(4, "big")))
        if state == sm.RUNNING:
            await self.send([sm.RUN])

    async def body(self):
        by_name = {v: k for k, v in sm.NAMES.items()}
        for hole in self.cov.holes():
            if not hole.startswith("cmd "):
                continue
            _, name, _, state = hole.split()
            op = by_name.get(name, self.rng.choice(UNKNOWN_OPS))
            await self.goto(sm.STATE_NAMES.index(state))
            await self.send([op] + payload_for(op, self.rng))


class TopSeq(BaseSeq):
    """Sessions: sometimes a reset, a load (good or faulty), maybe RUN + traffic, random commands."""

    def __init__(self, name, rng, sessions):
        super().__init__(name)
        self.rng, self.sessions = rng, sessions

    async def body(self):
        r = self.rng
        await self.reset()
        await self.send([sm.READ_ID, 0, 0, 0, 0])
        for s in range(self.sessions):
            if r.random() < 0.25:
                await self.reset()
            if r.random() < 0.1:                    # partial opcode: discarded
                await self.send([r.randrange(256)], nbits=r.randint(1, 7))
            await RandomCmdSeq("rand", r, r.randint(0, 4)).start(self.sequencer)
            await LoadSeq("load", r).start(self.sequencer)
            if r.random() < 0.5:                    # commands in LOADED / LOADING / ERROR
                await RandomCmdSeq("rand", r, r.randint(1, 3)).start(self.sequencer)
            await RunTrafficSeq("run", r, r.randint(2, 25)).start(self.sequencer)
            await RandomCmdSeq("rand", r, r.randint(0, 3)).start(self.sequencer)


# ---- agents ---------------------------------------------------------------------------------
class Driver(uvm_driver):
    def build_phase(self):
        self.dut = cocotb.top
        self.events = uvm_analysis_port("events", self)

    def start_of_simulation_phase(self):
        d = self.dut
        d.host_cs_n.value = 1
        d.host_sck.value = 0
        d.host_mosi.value = 0

    async def spi(self, it):
        d = self.dut
        nbits = 8 * len(it.mosi) if it.nbits is None else it.nbits
        d.host_cs_n.value = 0
        await ClockCycles(d.clk, LEAD)
        bits = [(b >> (7 - k)) & 1 for b in it.mosi for k in range(8)][:nbits]
        miso = 0
        for i, bit in enumerate(bits):
            d.host_mosi.value = bit
            await ClockCycles(d.clk, HALF)
            miso = (miso << 1) | int(d.host_miso.value)
            d.host_sck.value = 1
            await ClockCycles(d.clk, HALF)
            d.host_sck.value = 0
            if i % 8 == 7:
                it.miso.append(miso)
                miso = 0
        await ClockCycles(d.clk, HALF)
        d.host_cs_n.value = 1
        await ClockCycles(d.clk, GAP)

    async def run_phase(self):
        d = self.dut
        while True:
            it = await self.seq_item_port.get_next_item()
            if it.kind == "spi":
                await self.spi(it)
            elif it.kind == "reset":
                d.rst_n.value = 0
                await ClockCycles(d.clk, 4)
                d.rst_n.value = 1
                self.events.write(("reset",))
                await ClockCycles(d.clk, GAP)
            else:
                self.events.write(("fabric", it.status, it.attention))
                ConfigDB().get(self, "", "fabric_agent").set_design(it.status, it.attention)
                await ClockCycles(d.clk, GAP)
            self.seq_item_port.item_done()


class SpiMonitor(uvm_component):
    """Passive: samples the pins every clk, decodes one transaction per CS_N low period."""

    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)
        self.dut = cocotb.top

    async def run_phase(self):
        d = self.dut
        cs_prev, sck_prev = 1, 0
        while True:
            await RisingEdge(d.clk)
            cs, sck = int(d.host_cs_n.value), int(d.host_sck.value)
            if cs_prev and not cs:
                bits_o, bits_i, irq = [], [], val(d.host_irq, -1)
            elif not cs and sck and not sck_prev:
                bits_o.append(int(d.host_mosi.value))
                bits_i.append(val(d.host_miso))
            elif cs and not cs_prev:
                await ClockCycles(d.clk, SETTLE)
                n = len(bits_o)
                pack = lambda bits: [int("".join(map(str, bits[i:i + 8])), 2)  # noqa: E731
                                     for i in range(0, n - n % 8, 8)]
                mosi = pack(bits_o)
                if n % 8:                           # the partial byte, padded (not received)
                    mosi.append(int("".join(map(str, bits_o[n - n % 8:])).ljust(8, "0"), 2))
                self.ap.write(SpiTxn(mosi, pack(bits_i), n, irq))
                cs, sck = int(d.host_cs_n.value), int(d.host_sck.value)
            cs_prev, sck_prev = cs, sck


class CfgMonitor(uvm_component):
    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)

    async def run_phase(self):
        d = cocotb.top
        while True:
            await RisingEdge(d.clk)
            if val(d.cfg_strobe):
                self.ap.write(int(d.cfg_word.value))


class FabricAgent(uvm_component):
    """The user design side of the host channel: a one-byte loopback (accepts a host byte when
    empty, offers it back on the design → host channel), plus h_status / h_attention. Held in
    reset (empty, attention 0) whenever the shell holds the user design in reset."""

    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)    # (data, last) bytes the design accepted
        ConfigDB().set(None, "*", "fabric_agent", self)
        self.status, self.attention = 0, 0

    def set_design(self, status, attention):
        self.status, self.attention = status, attention

    async def run_phase(self):
        d = cocotb.top
        hold = None
        wready = rvalid = 0
        while True:
            d.h_wready.value = wready
            d.h_rvalid.value = rvalid
            d.h_rdata.value = hold[0] if hold else 0
            d.h_status.value = self.status
            in_reset = (not val(d.rst_n)) or val(d.user_reset, 1)
            d.h_attention.value = 0 if in_reset else self.attention
            await RisingEdge(d.clk)
            if (not val(d.rst_n)) or val(d.user_reset, 1):
                hold = None
            else:
                if rvalid and val(d.h_rready):
                    hold = None
                if wready and val(d.h_wvalid):
                    hold = (int(d.h_wdata.value), int(d.h_wlast.value))
                    self.ap.write(hold)
            wready, rvalid = int(hold is None), int(hold is not None)


# ---- checking -------------------------------------------------------------------------------
class LoopbackModel:
    """Model of FabricAgent at transaction level (settled between transactions)."""

    def __init__(self):
        self.hold, self.delivered = None, []
        self.status, self.attention = 0, 0

    def user_reset(self):
        self.hold = None

    def settle(self, m):
        while True:
            moved = False
            if self.hold is not None and len(m.rx) < sm.FIFO_DEPTH:
                m.rx.append(self.hold[0])
                self.hold, moved = None, True
            if self.hold is None and m.tx:
                self.hold = m.tx.pop(0)
                self.delivered.append(self.hold)
                moved = True
            if not moved:
                return


class Scoreboard(uvm_component):
    def build_phase(self):
        self.spi_fifo = uvm_tlm_analysis_fifo("spi_fifo", self)
        self.cfg_fifo = uvm_tlm_analysis_fifo("cfg_fifo", self)
        self.fab_fifo = uvm_tlm_analysis_fifo("fab_fifo", self)
        self.ev_fifo = uvm_tlm_analysis_fifo("ev_fifo", self)
        self.ap = uvm_analysis_port("ap", self)     # (state before, txn, expected) to coverage
        self.fabric = LoopbackModel()
        self.model = sm.ShellModel(ARCH, self.fabric)
        self.cfg_seen, self.fab_seen = [], []
        self.errors, self.checked, self.txns = [], 0, 0

    def fail(self, msg):
        self.errors.append(msg)
        self.logger.error(msg)

    def drain(self):
        ok, x = self.cfg_fifo.try_get()
        while ok:
            self.cfg_seen.append(x)
            ok, x = self.cfg_fifo.try_get()
        ok, x = self.fab_fifo.try_get()
        while ok:
            self.fab_seen.append(x)
            ok, x = self.fab_fifo.try_get()

    async def run_phase(self):
        while True:
            # events (reset, design status) and transactions arrive in simulation order
            ok, ev = self.ev_fifo.try_get()
            if ok:
                if ev[0] == "reset":
                    self.model.reset()
                else:
                    self.fabric.status, self.fabric.attention = ev[1], ev[2]
                continue
            ok, t = self.spi_fifo.try_get()
            if not ok:
                await RisingEdge(cocotb.top.clk)
                continue
            self.txns += 1
            self.drain()
            m = self.model
            before = m.state
            if t.irq != m.irq():
                self.fail(f"txn {self.txns}: HOST_IRQ {t.irq}, model {m.irq()} (state {before})")
            exp = m.transaction(t.mosi, t.nbits)
            for i, (got, want) in enumerate(zip(t.miso, exp)):
                if want is not None:
                    self.checked += 1
                    if got != want:
                        self.fail(f"txn {self.txns} {bytes(t.mosi[:6]).hex()} nbits={t.nbits}: "
                                  f"MISO byte {i} = 0x{got:02x}, model 0x{want:02x} "
                                  f"(state before {sm.STATE_NAMES[before]})")
            if self.cfg_seen != m.forwarded:
                self.fail(f"txn {self.txns}: configuration words differ: "
                          f"{len(self.cfg_seen)} seen, {len(m.forwarded)} expected")
                self.cfg_seen = list(m.forwarded)   # resynchronise to report later ones
            if self.fab_seen != self.fabric.delivered:
                self.fail(f"txn {self.txns}: design-side bytes differ: "
                          f"{self.fab_seen[-3:]} vs {self.fabric.delivered[-3:]}")
                self.fab_seen = list(self.fabric.delivered)
            self.ap.write((before, t, exp, m.code, m.status()))

    def check_phase(self):
        self.logger.info(f"scoreboard: {self.txns} transactions, {self.checked} response bytes "
                         f"compared, {len(self.cfg_seen)} configuration words, "
                         f"{len(self.fab_seen)} design-side bytes, {len(self.errors)} mismatches")
        assert not self.errors, f"{len(self.errors)} mismatches; first: {self.errors[0]}"
        assert self.txns > 0


class Coverage(uvm_subscriber):
    """Functional coverage. Bins: every opcode (and 'unknown') in every state; every ERROR_CODE
    value read back; every STATUS flag seen set; aborted transactions of each kind; loads."""

    def build_phase(self):
        ops = [sm.NAMES[o] for o in sm.OPCODES] + ["UNKNOWN"]
        self.bins = {}
        for o in ops:
            for s in sm.STATE_NAMES:
                self.bins[f"cmd {o} in {s}"] = 0
        for c in (0x00, 0x01, 0x10, 0x11, 0x12, 0x13):
            self.bins[f"ERROR_CODE 0x{c:02x} read"] = 0
        for b, name in ((4, "rx_valid"), (3, "tx_ready"), (2, "ch_overflow"),
                        (1, "user_attention"), (0, "error_pending")):
            self.bins[f"STATUS.{name} set"] = 0
        self.bins["STATUS.tx_ready clear (channel full)"] = 0
        for k in ("partial opcode", "LOAD_DATA mid-word", "LOAD_END mid-CRC", "CH_WRITE mid-payload"):
            self.bins[f"abort: {k}"] = 0
        self.bins["HOST_IRQ high"] = 0
        self.bins["load reaches LOADED"] = 0
        self.bins["full channel loop (5 bytes in flight)"] = 0

    def hit(self, name):
        self.bins[name] += 1

    def holes(self):
        return [k for k, v in self.bins.items() if not v]

    def snapshot(self):
        self.random_hit = sum(1 for v in self.bins.values() if v)

    def write(self, t):
        before, txn, exp, code, status = t
        n = txn.nbits
        if n < 8:
            self.hit("abort: partial opcode")
            return
        op = txn.mosi[0]
        name = sm.NAMES.get(op, "UNKNOWN")
        self.hit(f"cmd {name} in {sm.STATE_NAMES[before]}")
        st = txn.miso[0]
        for b, fname in ((4, "rx_valid"), (3, "tx_ready"), (2, "ch_overflow"),
                         (1, "user_attention"), (0, "error_pending")):
            if (st >> b) & 1:
                self.hit(f"STATUS.{fname} set")
        if not (st >> 3) & 1:
            self.hit("STATUS.tx_ready clear (channel full)")
        if txn.irq:
            self.hit("HOST_IRQ high")
        if op == sm.READ_STATUS and len(txn.miso) >= 3:
            key = f"ERROR_CODE 0x{txn.miso[2]:02x} read"
            if key in self.bins:
                self.hit(key)
        full = 8 * len(txn.mosi)
        if n < full and before in sm.ALLOWED.get(op, ()):
            if op == sm.LOAD_DATA and n % 32 != 8:
                self.hit("abort: LOAD_DATA mid-word")
            elif op == sm.LOAD_END:
                self.hit("abort: LOAD_END mid-CRC")
            elif op == sm.CH_WRITE:
                self.hit("abort: CH_WRITE mid-payload")
        if op == sm.LOAD_END and n == full and (status >> 5) == sm.LOADED:
            self.hit("load reaches LOADED")
        if (st >> 3) & 1 == 0 and (st >> 4) & 1:
            self.hit("full channel loop (5 bytes in flight)")

    def report_phase(self):
        hit = sum(1 for v in self.bins.values() if v)
        pct = 100.0 * hit / len(self.bins)
        holes = [k for k, v in self.bins.items() if not v]
        self.logger.info(f"functional coverage: {hit}/{len(self.bins)} bins ({pct:.1f}%); "
                         f"{self.random_hit} from random sessions, the rest from closure")
        for h in holes:
            self.logger.warning(f"coverage hole: {h}")
        out = Path(os.environ.get("UVM_COVERAGE_OUT", "sim_build/uvm_coverage.json"))
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"seed": cocotb.RANDOM_SEED, "bins": self.bins, "hit": hit,
                                   "random_hit": self.random_hit, "total": len(self.bins)},
                                  indent=1))
        assert not holes, f"{len(holes)} coverage holes: {holes[:5]}"


class Env(uvm_env):
    def build_phase(self):
        self.seqr = uvm_sequencer("seqr", self)
        ConfigDB().set(None, "*", "SEQR", self.seqr)
        self.fabric_agent = FabricAgent("fabric_agent", self)
        self.driver = Driver("driver", self)
        self.spi_mon = SpiMonitor("spi_mon", self)
        self.cfg_mon = CfgMonitor("cfg_mon", self)
        self.sb = Scoreboard("sb", self)
        self.cov = Coverage("cov", self)
        ConfigDB().set(None, "*", "COV", self.cov)

    def connect_phase(self):
        self.driver.seq_item_port.connect(self.seqr.seq_item_export)
        self.driver.events.connect(self.sb.ev_fifo.analysis_export)
        self.spi_mon.ap.connect(self.sb.spi_fifo.analysis_export)
        self.cfg_mon.ap.connect(self.sb.cfg_fifo.analysis_export)
        self.fabric_agent.ap.connect(self.sb.fab_fifo.analysis_export)
        self.sb.ap.connect(self.cov.analysis_export)


@pyuvm.test()
class ShellRandomTest(uvm_test):
    """Constrained-random sessions (loads with injected faults, runs with channel traffic,
    random commands, resets); every response checked; coverage must reach 100%."""

    def build_phase(self):
        self.env = Env("env", self)

    async def run_phase(self):
        self.raise_objection()
        d = cocotb.top
        d.rst_n.value = 0
        cocotb.start_soon(Clock(d.clk, 20, unit="ns").start())
        await ClockCycles(d.clk, 5)
        d.rst_n.value = 1
        rng = random.Random(cocotb.RANDOM_SEED)
        sessions = int(os.environ.get("UVM_ITEMS", "60"))
        self.logger.info(f"seed {cocotb.RANDOM_SEED}, {sessions} sessions")
        seqr = ConfigDB().get(self, "", "SEQR")
        cov = ConfigDB().get(self, "", "COV")
        await TopSeq("top", rng, sessions).start(seqr)
        await ClockCycles(d.clk, 2 * GAP)            # let the last transactions reach coverage
        cov.snapshot()
        self.logger.info(f"random sessions: {cov.random_hit}/{len(cov.bins)} bins; "
                         f"closing {len(cov.holes())} holes")
        await ClosureSeq("closure", rng, cov).start(seqr)
        await ClockCycles(d.clk, 2 * GAP)
        self.drop_objection()

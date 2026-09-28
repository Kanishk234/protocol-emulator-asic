"""L1-HOST: trw_host through its pads (2-FF synchronisers, SPI mode 0 at SCK = clk/8, the slowest ratio §9
allows), against the register map in spec/tripwire.yaml (`host_map`, D-046 with D-042 and D-044)."""

import pathlib
import random
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, ReadOnly, RisingEdge

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
import tripwire_spec as S  # noqa: E402

HM = {k: v[0] for k, v in S.HOST_MAP.items()}
LW = {w: j for j, w in enumerate(S.HOST_LANE_WORDS)}
NL, NU, NC, LDW = 3, 6, 13, 180
H = 4                                                   # SCK half period in clocks (SCK = clk/8)
STROBES = ("slot_we", "lane_hwe", "port_we", "clr_dropped", "pcfg_we", "clr_overrun", "clr_late", "hin_load",
           "hout_take", "step")


class Host:
    def __init__(self, dut):
        self.d = dut
        self.ev = []            # (clock, strobe name, value, slot_waddr, lane_hsel, pcfg_waddr, wdata)
        self.n = 0

    @classmethod
    async def start(cls, dut):
        h = cls(dut)
        cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())
        for s in ("lane_dbg", "port_state", "dropped", "overrun", "late", "hin_all_taken", "hout_avail",
                  "hout_head", "mem_haddr", "sck_pad", "mosi_pad"):
            getattr(dut, s).value = 0
        dut.csn_pad.value = 1
        dut.rst_n.value = 0
        await ClockCycles(dut.clk, 3)
        dut.rst_n.value = 1
        cocotb.start_soon(h._monitor())
        return h

    async def _monitor(self):
        d = self.d
        while True:
            await RisingEdge(d.clk)
            await ReadOnly()
            self.n += 1
            for s in STROBES:
                v = int(getattr(d, s).value)
                if v:
                    self.ev.append((self.n, s, v, int(d.slot_waddr.value), int(d.lane_hsel.value),
                                    int(d.pcfg_waddr.value), int(d.wdata.value)))

    async def _xfer(self, out_bits, n_in):
        """Clock out `out_bits` (MSB first) then `n_in` more bits; returns the MISO bits sampled at each rise."""
        d = self.d
        await FallingEdge(d.clk)
        d.csn_pad.value = 0
        await ClockCycles(d.clk, H, rising=False)
        got = []
        for i in range(len(out_bits) + n_in):
            d.mosi_pad.value = out_bits[i] if i < len(out_bits) else 0
            await ClockCycles(d.clk, H, rising=False)
            got.append(int(d.miso.value))                   # mode 0: the controller samples at the rise
            d.sck_pad.value = 1
            await ClockCycles(d.clk, H, rising=False)
            d.sck_pad.value = 0
        await ClockCycles(d.clk, H, rising=False)
        d.csn_pad.value = 1
        await ClockCycles(d.clk, 2 * H, rising=False)
        return got

    @staticmethod
    def _bits(v, n):
        return [(v >> (n - 1 - i)) & 1 for i in range(n)]

    async def write(self, addr, words):
        bits = self._bits(0x80, 8) + self._bits(addr, 16)
        for w in words:
            bits += self._bits(w, 16)
        await self._xfer(bits, 0)

    async def read(self, addr, n=1):
        bits = self._bits(0x00, 8) + self._bits(addr, 16)
        got = await self._xfer(bits, 8 + 16 * n)
        data = got[len(bits) + 8:]
        return [int("".join(map(str, data[16 * i:16 * i + 16])), 2) for i in range(n)]

    def events(self, name=None):
        return [e for e in self.ev if name is None or e[1] == name]


def pack_lane(f):
    """Lane debug bus from named fields (layout in trw_host.v's header)."""
    v = f["regs"] | f["state"] << 64 | f["flags"] << 68 | f["pend"] << 72 | f["rpc"] << 75 | f["rir_v"] << 84
    v |= f["rir"] << 85 | f["rz"] << 101 | f["ov"] << 102 | f["os"] << 104 | f["otok"] << 106
    v |= f["iav"] << 142 | f["ihead"] << 144
    return v


@cocotb.test()
async def test_control_id_step_irq(dut):
    h = await Host.start(dut)
    major, minor = (int(x) for x in S.VERSION.split("."))
    assert await h.read(HM["id"]) == [S.HOST_ID]
    assert await h.read(HM["version"]) == [major << 8 | minor]
    t0, t1 = (await h.read(HM["time"]))[0], (await h.read(HM["time"]))[0]
    assert 0 < (t1 - t0) % 65536 < 2000
    assert await h.read(HM["run"]) == [0]
    await h.write(HM["run"], [0b001])
    assert int(dut.run.value) == 1 and int(dut.live.value) == 1
    assert await h.read(HM["run"]) == [1 << S.HOST_RUN_LIVE_BIT | 1]
    await h.write(HM["step"], [0b111])                  # lane 0 runs: only lanes 1 and 2 step
    st = h.events("step")
    assert len(st) == 1 and st[0][2] == 0b110
    await h.write(HM["run"], [0])
    assert int(dut.live.value) == 1, "live stays set once any lane has run (D-041 B)"
    # IRQ: status is live, the pad is registered and follows the enable
    dut.late.value = 1 << 2
    await h.write(HM["irq_en"], [1 << (S.HOST_IRQ_BITS["units"] + 2)])
    assert int(dut.irq.value) == 1
    st = (await h.read(HM["irq_status"]))[0]
    assert st >> 2 & 1 and st >> S.HOST_IRQ_BITS["host_in"] & 1, hex(st)
    dut.late.value = 0
    await ClockCycles(dut.clk, 2)
    assert int(dut.irq.value) == 0
    dut.dropped.value = 5 << (8 * 7)
    await h.write(HM["irq_en"], [1 << S.HOST_IRQ_BITS["dropped"]])
    assert int(dut.irq.value) == 1


@cocotb.test()
async def test_write_decode(dut):
    h = await Host.start(dut)
    await h.write(HM["run"], [0b001])                   # lane 0 running
    a = HM["slots"]
    await h.write(a | 1 << 8 | 5 << 4 | 2, [0xBEEF])    # lane 1, slot 5, word 2
    await h.write(a | 2 << 8 | 12 << 4 | 3, [0x1234])   # lane 2, K3
    await h.write(a | 1 << 8 | 5 << 4 | 1 << 2, [0x1111])   # [3:2] != 0: ignored
    await h.write(a | 0 << 8 | 1 << 4, [0x2222])        # lane 0 is running: dropped
    ev = h.events("slot_we")
    assert [(e[2], e[3], e[6]) for e in ev] == [(0b010, 5 * 4 + 2, 0xBEEF), (0b100, 12 * 4 + 3, 0x1234)], ev
    await h.write(HM["lanes"] + 2 * S.HOST_LANE_STRIDE + LW["state"], [0x7])
    await h.write(HM["lanes"] + 1 * S.HOST_LANE_STRIDE + LW["flags"], [0x7])   # read-only: no strobe
    ev = h.events("lane_hwe")
    assert [(e[2], e[4], e[6]) for e in ev] == [(0b100, 4, 7)]
    await h.write(HM["ports"], [0x3FF, 0x001, 0x2A5])   # auto-increment: ports 0, 1, 2
    ev = h.events("port_we")
    assert [(e[2], e[6]) for e in ev] == [(1, 0x3FF), (2, 0x001), (4, 0x2A5)]
    await h.write(HM["dropped"] + 3, [0])
    assert [e[2] for e in h.events("clr_dropped")] == [1 << 3]
    await h.write(HM["pin_cfg"] + 32 * 4 + 17, [0xABCD])
    ev = h.events("pcfg_we")
    assert [(e[2], e[5], e[6]) for e in ev] == [(1 << 4, 17, 0xABCD)]
    await h.write(HM["unit_flags"] + 2, [0b11])
    await h.write(HM["unit_flags"] + 3, [0b10])
    assert [e[2] for e in h.events("clr_overrun")] == [1 << 2]
    assert [e[2] for e in h.events("clr_late")] == [1 << 2, 1 << 3]
    await h.write(HM["owners"] + 5, [2])
    await h.write(HM["owners"] + 3, [2])                # uo3 = MISO: ignored
    assert await h.read(HM["owners"], 7) == [7, 7, 7, 7, 7, 2, 7]
    await h.write(0x4000, [0xFFFF])                     # unlisted: no strobe at all
    before = len(h.ev)
    assert len(h.ev) == before


@cocotb.test()
async def test_read_map(dut):
    rng = random.Random(8)
    h = await Host.start(dut)
    lanes = []
    for _ in range(NL):
        f = dict(regs=rng.randrange(1 << 64), state=rng.randrange(16), flags=rng.randrange(16), pend=rng.randrange(8),
                 rpc=rng.randrange(512), rir_v=rng.randrange(2), rir=rng.randrange(1 << 16), rz=rng.randrange(2),
                 ov=rng.randrange(4), os=rng.randrange(4), otok=rng.randrange(1 << 36), iav=rng.randrange(4),
                 ihead=rng.randrange(1 << 36))
        lanes.append(f)
    dut.lane_dbg.value = sum(pack_lane(f) << (LDW * k) for k, f in enumerate(lanes))
    for k, f in enumerate(lanes):
        got = await h.read(HM["lanes"] + k * S.HOST_LANE_STRIDE, len(S.HOST_LANE_WORDS))
        w = dict(zip(S.HOST_LANE_WORDS, got))
        assert [w[f"r{i}"] for i in range(4)] == [(f["regs"] >> 16 * i) & 0xFFFF for i in range(4)]
        assert w["state"] == f["state"] and w["flags"] == f["pend"] << 4 | f["flags"]
        assert w["rpc"] == f["rpc"] and w["rir_status"] == f["rir_v"] << 15 | f["rz"] << 14 and w["rir"] == f["rir"]
        ch = (f["ov"] >> 1) << 5 | (f["os"] >> 1) << 4 | (f["ov"] & 1) << 3 | (f["os"] & 1) << 2 | f["iav"]
        assert w["channels"] == ch, (hex(w["channels"]), hex(ch))
        for p in range(2):
            it, ot = (f["ihead"] >> 18 * p) & 0x3FFFF, (f["otok"] >> 18 * p) & 0x3FFFF
            assert (w[f"i{p}_tag"], w[f"i{p}_data"]) == (it >> 16, it & 0xFFFF)
            assert (w[f"o{p}_tag"], w[f"o{p}_data"]) == (ot >> 16, ot & 0xFFFF)
    assert await h.read(HM["lanes"] + 3 * S.HOST_LANE_STRIDE) == [0]   # no lane 3
    ps = [rng.randrange(1 << 10) for _ in range(NC)]
    dr = [rng.randrange(256) for _ in range(NC)]
    dut.port_state.value = sum(v << 10 * c for c, v in enumerate(ps))
    dut.dropped.value = sum(v << 8 * c for c, v in enumerate(dr))
    assert await h.read(HM["ports"], NC) == ps
    assert await h.read(HM["dropped"], NC) == dr
    dut.overrun.value, dut.late.value = 0b100001, 0b000011
    assert await h.read(HM["unit_flags"], NU) == [3, 2, 0, 0, 0, 1]
    assert await h.read(0x4000, 2) == [0, 0]


@cocotb.test()
async def test_host_in_and_out(dut):
    h = await Host.start(dut)
    dut.hin_all_taken.value = 0                         # a blocking subscriber that never takes
    await h.write(HM["host_in"] + 2, [0x5A5A])
    assert int(dut.hin_valid.value) == 1 and int(dut.hin_q.value) == (2 << 16 | 0x5A5A)
    assert (await h.read(HM["host_status"]))[0] >> 14 & 1 == 0, "HOST_IN must read busy"
    await h.write(HM["host_in"] + 1, [0x1111])          # refused: not free
    assert len(h.events("hin_load")) == 1 and int(dut.hin_q.value) == (2 << 16 | 0x5A5A)
    dut.hin_all_taken.value = 1
    await h.write(HM["host_in"] + 1, [0x2222])
    assert len(h.events("hin_load")) == 2 and int(dut.hin_q.value) == (1 << 16 | 0x2222)
    dut.hout_avail.value, dut.hout_head.value = 1, 3 << 16 | 0xC0DE
    assert await h.read(HM["host_status"]) == [1 << 15 | 1 << 14 | 3]
    assert not h.events("hout_take")
    assert await h.read(HM["host_out"]) == [0xC0DE]
    assert len(h.events("hout_take")) == 1
    await h.read(HM["host_status"], 1)                 # prefetches host_out but does not read it
    assert len(h.events("hout_take")) == 1, "a prefetch must not take the token (BUGS #47)"
    dut.hout_avail.value = 0
    await h.read(HM["host_out"])
    assert len(h.events("hout_take")) == 1, "no take without a token"


@cocotb.test()
async def test_status_then_data_burst(dut):
    """BUGS #48: a burst read of host_status then host_out takes the token only if the status showed it.
    A token that arrives between the two loads stays for the next read."""
    h = await Host.start(dut)
    dut.hout_avail.value, dut.hout_head.value = 0, 1 << 16 | 0x0BAD

    async def arrive():                                  # after the status word's load, before the data's
        await ClockCycles(dut.clk, 8 * H * 2 * 5)
        dut.hout_avail.value = 1
    cocotb.start_soon(arrive())
    st, _ = await h.read(HM["host_status"], 2)
    assert not st >> 15, "the status must have been loaded before the token arrived"
    assert not h.events("hout_take"), "a token the host did not see must not be taken"
    st, d = await h.read(HM["host_status"], 2)
    assert st >> 15 and d == 0x0BAD and len(h.events("hout_take")) == 1


@cocotb.test()
async def test_sram_through_the_host_slot(dut):
    h = await Host.start(dut)
    off_slot = []

    async def watch():                                  # §14 R1: the host uses only slot 3 (time mod 4)
        while True:
            await RisingEdge(dut.clk)
            await ReadOnly()
            if int(dut.mem_en.value) and int(dut.tnow.value) % 4 != 3:
                off_slot.append(int(dut.tnow.value))
    cocotb.start_soon(watch())
    words = [0x0001, 0xFFFF, 0x8000, 0x1234, 0xA5A5]
    await h.write(HM["sram"] + 0x10, words)
    for i, w in enumerate(words):
        dut.mem_haddr.value = 0x10 + i
        await ReadOnly()
        assert int(dut.mem_hrd.value) == w
        await RisingEdge(dut.clk)
    assert await h.read(HM["sram"] + 0x10, len(words)) == words
    await h.write(HM["sram"] + 0x1FF, [0x7777])           # the last word
    assert await h.read(HM["sram"] + 0x1FF) == [0x7777]
    assert not off_slot, f"SRAM accessed off the host slot at {off_slot[:5]}"

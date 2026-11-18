"""L3B-PEER: an unmodified third-party RTL controller drives the chip's I2C pins."""
import cocotb
from cocotb.triggers import ClockCycles, FallingEdge, ReadOnly, RisingEdge

from chiplib import hex_bytes, load, sigrok, start, write_vcd


class Peer:
    def __init__(self, dut):
        self.d = dut
        self.received = []
        self.nacks = 0
        self.rec = {'scl': [], 'sda': []}
        self.periods, self.highs, self.lows = [], [], []
        self.previous = (1, 1)
        self.in_frame = False
        self.candidate = self.last_rise = self.last_fall = None
        self.task = cocotb.start_soon(self.monitor())

    async def monitor(self):
        d = self.d
        while True:
            await FallingEdge(d.clk)
            await ReadOnly()
            assert d.uio_bus.value.is_resolvable
            bus = int(d.uio_bus.value)
            self.observe_clock(bus >> 1 & 1, bus & 1)
            self.rec['scl'].append(bus >> 1 & 1)
            self.rec['sda'].append(bus & 1)
            assert not (int(d.uio_out.value) & int(d.uio_oe.value) & 1), 'Target drove SDA high'
            assert not (int(d.uio_oe.value) & 2), 'Target drove SCL'
            assert int(d.peer_sda_t.value) or not int(d.peer_sda_o.value), 'Peer drove SDA high'
            assert int(d.peer_scl_t.value) or not int(d.peer_scl_o.value), 'Peer drove SCL high'
            if int(d.read_valid.value):
                self.received.append((int(d.data_out.value), bool(d.read_last.value)))
            if int(d.peer_missed_ack.value):
                self.nacks += 1

    def observe_clock(self, scl, sda):
        clock = len(self.rec['scl'])
        previous_scl, previous_sda = self.previous
        if scl and previous_scl and sda != previous_sda:
            self.in_frame = not sda  # START/repeated START or STOP
            self.candidate = self.last_rise = self.last_fall = None
        elif self.in_frame:
            if scl and not previous_scl:
                self.candidate = (clock, self.last_fall)
            elif not scl and previous_scl:
                # Confirm a data/ACK clock only once it ends without START/STOP.
                if self.candidate is not None:
                    rise, fall = self.candidate
                    self.highs.append(clock - rise)
                    if fall is not None: self.lows.append(rise - fall)
                    if self.last_rise is not None: self.periods.append(rise - self.last_rise)
                    self.last_rise = rise
                    self.candidate = None
                self.last_fall = clock
        self.previous = scl, sda

    async def handshake(self, valid, ready, values):
        d = self.d
        await FallingEdge(d.clk)
        for name, value in values.items():
            getattr(d, name).value = value
        getattr(d, valid).value = 1
        for _ in range(100_000):
            await ReadOnly()
            accepted = bool(int(getattr(d, ready).value))
            await RisingEdge(d.clk)
            if accepted:
                await FallingEdge(d.clk)
                getattr(d, valid).value = 0
                return
            await FallingEdge(d.clk)
        raise AssertionError(f'Independent peer {ready} timed out')

    async def command(self, addr, *, read=False, write=False, stop=True):
        await self.handshake('cmd_valid', 'cmd_ready', dict(
            cmd_address=addr, cmd_start=0, cmd_read=int(read), cmd_write=0,
            cmd_write_multiple=int(write), cmd_stop=int(stop)))

    async def idle(self):
        for _ in range(2000):
            await ClockCycles(self.d.clk, 50)
            if not (int(self.d.peer_busy.value) or int(self.d.peer_bus_control.value)
                    or int(self.d.peer_bus_active.value)):
                return
        raise AssertionError('Independent controller did not issue STOP/release bus')

    async def write(self, addr, payload, *, stop=True):
        assert payload
        await self.command(addr, write=True, stop=stop)
        for index, value in enumerate(payload):
            await self.handshake('data_valid', 'data_ready',
                                 dict(data_in=value, data_last=int(index == len(payload)-1)))
        if stop:
            await self.idle()

    async def read(self, addr, count):
        offset = len(self.received)
        for index in range(count):
            await self.command(addr, read=True, stop=index == count-1)
        await self.idle()
        result = self.received[offset:]
        assert len(result) == count, result
        assert [last for _, last in result] == [False]*(count-1) + [True], result
        return [value for value, _ in result]

    async def random_read(self, addr, pointer, count):
        await self.write(addr, [pointer], stop=False)
        return await self.read(addr, count)


def initialize(dut, prescale):
    for name in ['cmd_address', 'cmd_start', 'cmd_read', 'cmd_write', 'cmd_write_multiple',
                 'cmd_stop', 'cmd_valid', 'data_in', 'data_valid', 'data_last']:
        getattr(dut, name).value = 0
    dut.read_ready.value = 1
    dut.prescale.value = prescale


async def exercise_peer(dut, program):
    """Page write/read, repeated START, controller NACK, wrong address and wrap."""
    for index, prescale in enumerate((31, 11)):
        initialize(dut, prescale)
        p = await start(dut, uio=0xFF, clock=index == 0)
        await load(p, program)
        peer = Peer(dut)
        try:
            await peer.write(0x50, [0x20, 0x11, 0xA5, 0x00, 0xFF])
            assert await peer.random_read(0x50, 0x20, 4) == [0x11, 0xA5, 0x00, 0xFF]
            assert await peer.read(0x50, 1) == [0xFF]
            assert peer.nacks == 0, peer.nacks
            # The independent core continues after NACK: all three bytes must be ignored.
            await peer.write(0x51, [0x20, 0x99])
            assert peer.nacks == 3, peer.nacks
            assert await peer.random_read(0x50, 0x20, 1) == [0x11]
            await peer.write(0x50, [6, 0x31, 0x42, 0x53, 0x64])
            assert await peer.random_read(0x50, 0, 2) == [0x53, 0x64]
            assert await peer.random_read(0x50, 6, 2) == [0x31, 0x42]
            await peer.write(0x50, [0xFF, 0x7E])
            assert await peer.random_read(0x50, 0xFF, 3) == [0x7E, 0x53, 0x64]
            assert await peer.read(0x50, 1) == [0xFF]
            assert peer.nacks == 3, peer.nacks
        finally:
            peer.task.cancel()
        path = f'{program}_peer_{prescale}.vcd'
        write_vcd(path, peer.rec)
        decoded = sigrok(path, 'i2c:scl=scl:sda=sda', 'i2c')
        assert decoded is not None, 'Independent sigrok decode is required'
        assert hex_bytes(decoded, 'Data read: ') == [v for v, _ in peer.received], decoded
        assert peer.periods and peer.highs and peer.lows
        if prescale == 31:
            assert min(peer.periods) >= 125 and min(peer.highs) >= 30 and min(peer.lows) >= 65
        else:
            assert min(peer.periods) == 50, 'Fast peer must actually reach 1 MHz'
            assert min(peer.highs) >= 13 and min(peer.lows) >= 25
        dut._log.info('Independent RTL peer prescale=%d: %d read bytes, %d expected NACKs; minimum period/high/low=%d/%d/%d clocks',
                      prescale, len(peer.received), peer.nacks, min(peer.periods), min(peer.highs), min(peer.lows))


@cocotb.test()
async def test_eeprom_against_independent_controller(dut):
    await exercise_peer(dut, 'i2c_target_eeprom')


@cocotb.test()
async def test_guard_against_independent_controller(dut):
    await exercise_peer(dut, 'i2c_target_eeprom_guard')

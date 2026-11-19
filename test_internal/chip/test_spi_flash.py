"""SPI READ/FAST_READ memory personality, using only chip pins (RTL or GL)."""
import cocotb
from cocotb.triggers import ClockCycles

from chiplib import start, load, Wire, write_vcd, sigrok, hex_bytes
from protomodels.spi import SPIController
from protomodels.spi_flash import read_request, response, FlashWireMonitor


MEMORY = bytes(((73 * i + 19) ^ (i >> 1)) & 255 for i in range(256))


async def replay(dut, pins, transfers, half, label):
    ctrl = SPIController(half, gap=128, tcss=8)
    monitor = FlashWireMonitor(MEMORY, transfers)
    for req,bits in transfers:
        ctrl.transfer(req,bits)
    state = dict(clock=0, release=0, longest=0)

    def environment(uo, outputs, enables, bus):
        miso = outputs & 1 if enables & 1 else 1
        sck,mosi,cs = ctrl.step(miso)
        monitor.sample(state['clock'],sck,mosi,cs,miso,enables & 1)
        state['clock'] += 1
        state['release'] = state['release'] + 1 if cs and enables & 1 else 0
        state['longest'] = max(state['longest'],state['release'])
        return {0:mosi,1:sck,2:cs}, None

    wire = Wire(pins,environment,{'sck':lambda uo,bus:ctrl.sck,
                                'mosi':lambda uo,bus:ctrl.mosi,
                                'cs':lambda uo,bus:ctrl.cs,
                                'miso':lambda uo,bus:bus & 1})
    budget=sum((len(req)*8 if bits is None else bits)*2*half + 128 + 8 + 2*half
               for req,bits in transfers)+2000
    try:
        for _ in range(budget//100+2):
            if ctrl.done():
                break
            await ClockCycles(dut.clk,100)
        assert ctrl.done(), 'SPI memory pin waveform timed out'
        summary=monitor.finish()
    finally:
        wire.stop()
    assert state['longest'] <= 3, state
    for (request,bits),actual in zip(transfers,ctrl.results):
        complete=len(request) if bits is None else bits//8
        expected=response(MEMORY,request[:complete])
        assert len(actual)==complete
        assert all(e is None or e==a for e,a in zip(expected,actual))
    # Required independent decoder on unmodified complete-frame captures.
    # Abort framing is checked by the controller and wire oracle; decoder
    # handling of partial bytes is deliberately not relabelled as full bytes.
    simulator=cocotb.SIM_NAME.replace(' ','_').replace('/','_')
    path=f'spi_memory_{simulator}_{label}.vcd'
    write_vcd(path,wire.rec)
    if all(bits is None for _,bits in transfers):
        for cls,want in [('mosi-data',[b for req,_ in transfers for b in req]),
                         ('miso-data',[b for row in ctrl.results for b in row])]:
            decoded=sigrok(path,'spi:clk=sck:mosi=mosi:miso=miso:cs=cs',f'spi={cls}')
            assert decoded is not None, 'Required SPI decoder unavailable'
            assert hex_bytes(decoded,r'spi-\d+: ')==want,(cls,decoded)
    dut._log.info('SPI_MEMORY %s half=%d summary=%s',label,half,summary)


@cocotb.test()
async def test_spi_memory_reads(dut):
    for n,half in enumerate((50,75,100)):
        p=await start(dut,ui=4,clock=n==0)
        await load(p,'spi_target_flash')
        transfers=[(read_request(cmd,addr,12,dummy=dummy),None)
                   for cmd,addr,dummy in [(3,0,0),(11,0xFE,0xA5),(3,0x12347F,0),
                                          (11,1,0xFF)]]
        await replay(dut,p,transfers,half,f'reads_{half}')


@cocotb.test()
async def test_spi_memory_abort_recovery(dut):
    p=await start(dut,ui=4)
    await load(p,'spi_target_flash')
    transfers=[]
    for command in (3,11):
        for bits in (1,7,8,15,23,31,32,39,40,47,48):
            transfers.extend([(read_request(command,0xFC,8,dummy=0xA5),bits),
                              (read_request(11 if command==3 else 3,0x31,8,dummy=0x5A),None)])
    await replay(dut,p,transfers,50,'aborts')

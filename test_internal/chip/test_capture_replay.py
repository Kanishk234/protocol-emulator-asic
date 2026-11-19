"""Pinned real recordings replayed at the original rate, only chip ports."""
import cocotb
from cocotb.triggers import ClockCycles

from chiplib import start,load,Wire,HM,TAGS
from capture_replay import Capture,reference,normalized,pads


async def replay(dut,name):
    capture=Capture(name)
    expected,_=reference(name)
    ui,uio=pads(name,capture.levels(0))
    p=await start(dut,ui=sum(v<<b for b,v in ui.items()),uio=uio)
    image=await load(p,capture.spec['program'],**capture.spec['params'])
    clock=0
    def environment(uo,out,oe,bus):
        nonlocal clock
        assert oe==0, 'Passive replay drove a recorded bus'
        ui,uio=pads(name,capture.levels(clock));clock+=1
        return ui,{i:uio>>i&1 for i in range(8)}
    wire=Wire(p,environment,{})
    got=[]
    try:
        for _ in range(2000):
            token=await p.pop()
            if token is not None:got.append(token)
            if wire.clocks>capture.clocks+3000:break
        assert wire.clocks>=capture.clocks, 'Truncated recording replay'
        if name=='spi':
            assert image['sram'][32:96]==[0xFFFF]*64
            words=await p.read(HM['sram']+32,64)
            assert words[len(expected):]==[0xFFFF]*(64-len(expected))
            got=[(TAGS['DATA'],w) for w in words[:len(expected)]]
        assert normalized(name,got)==expected,(name,got,expected)
        unit=1 if name=='uart' else 0
        assert await p.read(0x0010+unit,1)==[0], 'RX status flags'
    finally:wire.stop()
    dut._log.info('REAL_CAPTURE name=%s samples=%d clocks=%d decoded_items=%d host_tokens=%d',name,len(capture.samples),capture.clocks,len(expected),len(got))


@cocotb.test()
async def test_real_uart_capture(dut):await replay(dut,'uart')


@cocotb.test()
async def test_real_i2c_capture(dut):await replay(dut,'i2c')


@cocotb.test()
async def test_real_spi_capture(dut):await replay(dut,'spi')

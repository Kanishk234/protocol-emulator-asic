"""L4-TAP whole-chip paired runs; no hierarchical signal access."""
import hashlib

import cocotb
from chiplib import start,Wire,HM
from host import load_sequence
import tripwire_spec as S
from kernels.metamorphic_tap import Scenario,image,TAP_PORT


async def execute(dut,protocol,rate,*,tap,clock=True):
    scenario=Scenario(protocol,rate,stretch=40 if protocol=='i2c' else 0,bad=protocol=='uart')
    p=await start(dut,ui=scenario.initial_ui,uio=scenario.initial_uio,clock=clock)
    compiled=image(protocol,rate,'tap' if tap else None)
    for addr,words in load_sequence(compiled):await p.write(addr,words)
    wire=Wire(p,scenario.step,{
        'protocol':lambda uo,bus:uo&scenario.mask,
        'bus':lambda uo,bus:bus,
        'tx':lambda uo,bus:uo&1,
    })
    delivery=[]
    try:
        for data,tag in scenario.commands:
            await p.push(data,tag)
            delivery.append((wire.clocks,tuple(p.outq)))
        while wire.clocks<scenario.clocks:
            await p.poll()
            delivery.append((wire.clocks,tuple(p.outq)))
        scenario.finish(list(p.outq),wire.rec['tx'])
    finally:wire.stop()
    dropped=(await p.read(HM['dropped']+list(S.FABRIC_CONSUMERS).index(TAP_PORT),1))[0]&255
    flags=await p.read(HM['unit_flags'],4)
    return wire.rec,delivery,dropped,flags


async def paired(dut,protocol,rate):
    baseline=await execute(dut,protocol,rate,tap=False)
    tapped=await execute(dut,protocol,rate,tap=True,clock=False)
    assert baseline[0]==tapped[0],f'{protocol}: pad waveform changed with tap'
    assert baseline[1]==tapped[1],f'{protocol}: observed host transaction/delivery timing changed'
    assert baseline[2]==0 and tapped[2]>0, 'Tap must actually miss tokens'
    assert baseline[3]==tapped[3], 'Pin flags changed'
    trace=hashlib.sha256(bytes(baseline[0]['protocol'])+bytes(baseline[0]['bus'])).hexdigest()
    dut._log.info('L4_TAP protocol=%s clocks=%d drops=%d observed_host_polls=%d trace=%s',
                  protocol,len(baseline[0]['protocol']),tapped[2],len(baseline[1]),trace)


@cocotb.test()
async def test_uart_tap_is_cycle_exact(dut):await paired(dut,'uart',460800)


@cocotb.test()
async def test_spi_tap_is_cycle_exact(dut):await paired(dut,'spi',10)


@cocotb.test()
async def test_i2c_tap_is_cycle_exact(dut):await paired(dut,'i2c',124)

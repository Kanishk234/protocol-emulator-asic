"""Cycle-exact logical permutation checks on chip ports; no timing normalization."""
import hashlib

import cocotb
from chiplib import start,Wire,HM
from host import load_sequence
from kernels.metamorphic_perm import image,scenario


async def execute(dut,protocol,rate,mapping,clock):
    scene=scenario(protocol,rate)
    p=await start(dut,ui=scene.initial_ui,uio=scene.initial_uio,clock=clock)
    compiled=image(protocol,rate,mapping)
    for address,words in load_sequence(compiled):await p.write(address,words)
    wire=Wire(p,scene.step,{'protocol':lambda uo,bus:uo&scene.mask,
                          'bus':lambda uo,bus:bus,'rx':lambda uo,bus:p.ui&1,
                          'tx':lambda uo,bus:uo&1})
    observations=[]
    try:
        for data,tag in scene.commands:
            await p.push(data,tag)
            observations.append((wire.clocks,tuple(p.outq)))
        while wire.clocks<scene.clocks:
            await p.poll()
            observations.append((wire.clocks,tuple(p.outq)))
        scene.finish(list(p.outq),wire.rec['tx'])
        assert await p.read(HM['unit_flags'],4)==[0]*4
    finally:wire.stop()
    return wire.rec,observations


async def paired(dut,protocol,rate):
    baseline=await execute(dut,protocol,rate,'baseline',True)
    moved=await execute(dut,protocol,rate,'both',False)
    assert baseline==moved,(protocol,'logical lane/unit permutation changed pad or host observation')
    trace=hashlib.sha256(b''.join(bytes(baseline[0][k]) for k in ['protocol','bus','rx','tx'])).hexdigest()
    dut._log.info('L4_PERM protocol=%s clocks=%d observed_host_checkpoints=%d trace=%s',
                  protocol,len(baseline[0]['protocol']),len(baseline[1]),trace)


@cocotb.test()
async def test_uart_lane_and_unit_permutation(dut):await paired(dut,'uart',460800)


@cocotb.test()
async def test_spi_lane_and_unit_permutation(dut):await paired(dut,'spi',10)


@cocotb.test()
async def test_i2c_target_lane_and_unit_permutation(dut):await paired(dut,'i2c',125)

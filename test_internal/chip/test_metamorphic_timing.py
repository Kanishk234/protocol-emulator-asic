"""Approved D-191 SCALE and native routine-PERM, chip ports only."""
import hashlib
import json
from pathlib import Path

import cocotb
from cocotb.triggers import ClockCycles
from chiplib import start,Wire,HM
from host import load_sequence
from kernels import metamorphic_scale as scale
from kernels import metamorphic_perm as perm


async def scale_run(dut,protocol,rate,clock):
    scene=scale.scene(protocol,rate)
    p=await start(dut,ui=scene.initial_ui,uio=scene.initial_uio,clock=clock)
    for addr,words in load_sequence(scale.image(protocol,rate)):await p.write(addr,words)
    probes={'uart':{'tx':lambda uo,bus:uo&1,'rx':lambda uo,bus:p.ui&1},
            'spi':{'clk':lambda uo,bus:uo&1,'mosi':lambda uo,bus:uo>>1&1,
                   'miso':lambda uo,bus:p.ui&1,'cs':lambda uo,bus:uo>>2&1},
            # Sample the actual resolved input presented to the synchronizer.
            'i2c':{'scl':lambda uo,bus:int(dut.uio_in.value)>>1&1,
                   'sda':lambda uo,bus:int(dut.uio_in.value)&1}}[protocol]
    wire=Wire(p,scene.step,probes)
    try:
        for data,tag in scene.commands:await p.push(data,tag)
        while wire.clocks<scene.clocks:await p.poll()
        scene.finish(list(p.outq),wire.rec.get('tx'))
        assert await p.read(HM['unit_flags'],4)==[0]*4
    finally:wire.stop()
    result=scale.metrics(protocol,rate,wire.rec)
    path=Path(f'L4_scale_{protocol}_{rate}_{cocotb.SIM_NAME.replace(" ","_")}.vcd')
    result['capture_sha256']=scale.audit(protocol,rate,wire.rec,path)
    dut._log.info('L4_SCALE_RUN %s',json.dumps({'protocol':protocol,'rate':rate,'metrics':result},sort_keys=True))
    return result


async def scaled_pair(dut,protocol,fast,slow):
    a=await scale_run(dut,protocol,fast,True)
    b=await scale_run(dut,protocol,slow,False)
    scale.compare(protocol,a,b)


@cocotb.test()
async def test_uart_programmed_scale(dut):await scaled_pair(dut,'uart',500000,250000)


@cocotb.test()
async def test_spi_programmed_scale(dut):await scaled_pair(dut,'spi',20,40)


@cocotb.test()
async def test_i2c_programmed_scale(dut):await scaled_pair(dut,'i2c',100,200)


async def routine_run(dut,mapping,warmup,clock):
    scene=perm.scenario('i2c_controller',124)
    p=await start(dut,ui=scene.initial_ui,uio=scene.initial_uio,clock=clock)
    if warmup:await ClockCycles(dut.clk,warmup)
    for addr,words in load_sequence(perm.image('i2c_controller',124,mapping)):await p.write(addr,words)
    phase=(await p.read(HM['time'],1))[0]&3
    wire=Wire(p,scene.step,{'scl':lambda uo,bus:bus>>1&1,
                          'sda':lambda uo,bus:bus&1})
    checkpoints=[]
    try:
        for data,tag in scene.commands:
            await p.push(data,tag);checkpoints.append((wire.clocks,tuple(p.outq)))
        while wire.clocks<scene.clocks:
            await p.poll();checkpoints.append((wire.clocks,tuple(p.outq)))
        scene.finish(list(p.outq))
        assert await p.read(HM['unit_flags'],4)==[0]*4
    finally:wire.stop()
    digest=hashlib.sha256(bytes(wire.rec['scl'])+bytes(wire.rec['sda'])).hexdigest()
    return wire.rec,checkpoints,phase,digest


@cocotb.test()
async def test_native_routine_permutation_with_matched_phase(dut):
    base=await routine_run(dut,'baseline',0,True)
    moved=await routine_run(dut,'both',1,False)
    unaligned=await routine_run(dut,'both',0,False)
    assert (moved[2]-1)%4==base[2], 'Relative SRAM grant phase was not matched'
    assert moved[:2]==base[:2], 'Phase-matched native routine trace/host observations differ'
    assert unaligned[2]==base[2], 'Unaligned control was accidentally phase shifted'
    dut._log.info('L4_ROUTINE_PHASE %s',json.dumps({'baseline_phase':base[2],
        'moved_phase':moved[2],'unaligned_phase':unaligned[2],
        'matched_trace_sha256':base[3],'moved_trace_sha256':moved[3],
        'unaligned_trace_sha256':unaligned[3],'unaligned_trace_equal':unaligned[0]==base[0],
        'unaligned_data_and_function_passed':True,'clocks':len(base[0]['scl'])},sort_keys=True))

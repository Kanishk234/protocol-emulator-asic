"""Two real lanes, pad loopback and random idle; exact gates reuse this port-only test."""
import json
from pathlib import Path

import cocotb
from cocotb.triggers import ClockCycles
from chiplib import start,Wire,HM
from host import load_sequence
from kernels.metamorphic_loop import Loop,image,audit

PAYLOAD=bytes([0,255,85,170])


async def execute(dut,protocol,rate,seed,clock):
    loop=Loop(protocol,rate,PAYLOAD,seed)
    p=await start(dut,ui=loop.initial_ui,uio=loop.initial_uio,clock=clock)
    compiled=image(protocol,rate)
    for addr,words in load_sequence(compiled):await p.write(addr,words)
    probes={'uart':{'tx':lambda uo,bus:uo&1,'rx':lambda uo,bus:p.ui&1},
            'spi':{'clk':lambda uo,bus:uo&1,'mosi':lambda uo,bus:uo>>1&1,
                   'miso':lambda uo,bus:p.ui&1,'cs':lambda uo,bus:uo>>2&1},
            'i2c':{'sda':lambda uo,bus:bus&1,'scl':lambda uo,bus:bus>>1&1,
                   'target_sda':lambda uo,bus:bus>>2&1}}[protocol]
    wire=Wire(p,loop.step,probes)
    try:
        for index,byte in enumerate(PAYLOAD):
            begin=wire.clocks
            for data,tag in loop.commands(byte):await p.push(data,tag)
            while not loop.frame_complete(index,p.outq,int(dut.uo_out.value)):
                assert wire.clocks-begin<loop.frame_budget,f'{protocol}: loop timeout'
                await p.poll()
            await ClockCycles(dut.clk,loop.guard+loop.extra_idle[index])
        decoded=loop.check(list(p.outq))
        flags=await p.read(HM['unit_flags'],4)
        assert flags==[0]*4,(protocol,flags)
    finally:wire.stop()
    path=Path(f'L4_loop_{protocol}_{seed}_{cocotb.SIM_NAME.replace(" ","_")}.vcd')
    observation=audit(protocol,rate,PAYLOAD,wire.rec,path)
    dut._log.info('L4_LOOP_IDLE %s',json.dumps({'protocol':protocol,'rate':rate,'seed':seed,
                  'bytes':len(PAYLOAD),'clocks':wire.clocks,'idle_clocks':sum(loop.extra_idle),
                  **observation},sort_keys=True))
    return decoded,observation


async def paired(dut,protocol,rate):
    baseline=await execute(dut,protocol,rate,None,True)
    idle=await execute(dut,protocol,rate,7129,False)
    assert baseline[0]==idle[0]==list(PAYLOAD)
    a,b=baseline[1]['frame_start_clocks'],idle[1]['frame_start_clocks']
    assert a[0]==b[0] and a[1:]!=b[1:], 'Idle must move actual later frame starts'


@cocotb.test()
async def test_uart_two_lane_loop_and_idle(dut):await paired(dut,'uart',460800)


@cocotb.test()
async def test_spi_two_lane_loop_and_idle(dut):await paired(dut,'spi',10)


@cocotb.test()
async def test_i2c_two_lane_loop_and_idle(dut):await paired(dut,'i2c',124)

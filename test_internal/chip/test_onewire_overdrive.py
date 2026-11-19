"""ROM-layer 1-Wire speed entry/exit and presence through chip ports only."""
import re

import cocotb
from cocotb.triggers import ClockCycles

from chiplib import start,load,Wire,write_vcd,sigrok
from protomodels.onewire_overdrive import OverdriveROMDevice
from tripsim.isa import TAG_CTRL, TAG_DATA
import tripwire_spec as S


async def drain(pins,count):
    result=[]
    for _ in range(1200):
        token=await pins.pop()
        if token is not None:result.append(token)
        if len(result)==count:break
        await ClockCycles(pins.d.clk,32)
    assert len(result)==count,('Timed out waiting for 1-Wire results',result)
    return result


def peer_wire(pins,device):
    def environment(uo,out,oe,bus):
        assert not out & oe & 1, 'Controller drove DQ high'
        return {},{0:device.step(bus & 1)}
    return Wire(pins,environment,{'dq':lambda uo,bus:bus & 1})


async def enter(dut,pins,device):
    await load(pins,'onewire_master',OVERDRIVE=0)
    await pins.push(0,TAG_CTRL)
    await pins.push(0x3C,TAG_DATA)
    await ClockCycles(dut.clk,90000)
    assert await drain(pins,1)==[(TAG_DATA,0)]
    assert device.overdrive and device.entries==1 and device.history==[(False,0x3C)]


async def read_rom(dut,pins,device,fast):
    await load(pins,'onewire_master',OVERDRIVE=int(fast))
    await pins.push(0,TAG_CTRL)
    await pins.push(0x33,TAG_DATA)
    for _ in range(8):await pins.push(1,TAG_CTRL)
    expected=[(TAG_DATA,0),*[(TAG_DATA,b) for b in device.rom]]
    assert await drain(pins,9)==expected
    await ClockCycles(dut.clk,6000)  # leave the last pin timeline idle before reconfiguration
    assert device.received==[0x33]
    assert await pins.read(S.HOST_MAP['unit_flags'][0],1)==[0]


@cocotb.test()
async def test_onewire_speed_entry_read_and_exit(dut):
    p=await start(dut,uio=0xFF)
    device=OverdriveROMDevice()
    wire=peer_wire(p,device)
    try:
        await enter(dut,p,device)
        await read_rom(dut,p,device,True)
        assert device.overdrive and [fast for fast,_ in device.resets]==[False,True]
        await read_rom(dut,p,device,False)
        assert not device.overdrive and [fast for fast,_ in device.resets]==[False,True,False]
    finally:
        wire.stop()
    simulator=cocotb.SIM_NAME.replace(' ','_').replace('/','_')
    path=f'onewire_speeds_{simulator}.vcd'
    write_vcd(path,wire.rec)
    decoded=sigrok(path,'onewire_link:owr=dq,onewire_network','onewire_network')
    assert decoded is not None, 'Required 1-Wire decoder unavailable'
    assert re.search(r'overdrive.*skip',decoded,re.I) and decoded.count('Read ROM')==2,decoded
    roms=re.findall(r'ROM: 0x([0-9a-fA-F]{16})',decoded)
    assert [int(r,16) for r in roms]==[int.from_bytes(bytes(device.rom),'little')]*2,decoded
    dut._log.info('ONEWIRE_SPEEDS resets=%s entries=%d ROM=%s',device.resets,device.entries,device.rom)


@cocotb.test()
async def test_onewire_entry_required_and_presence_corners(dut):
    p=await start(dut,uio=0xFF)
    device=OverdriveROMDevice()
    wire=peer_wire(p,device)
    try:
        await load(p,'onewire_master',OVERDRIVE=1)
        await p.push(0,TAG_CTRL)
        assert await drain(p,1)==[(TAG_DATA,1)]
        await ClockCycles(dut.clk,6000)
        assert not device.resets and not device.overdrive
        # Clear the incomplete standard-speed observation from the deliberately
        # wrong-speed reset through an actual standard reset, not a peer reset.
        await enter(dut,p,device)
        await load(p,'onewire_master',OVERDRIVE=1)
        for high,low in ((2,8),(2,24),(6,8),(6,24)):
            device.presence_high,device.presence_low=high*50,low*50
            await p.push(0,TAG_CTRL)
            assert await drain(p,1)==[(TAG_DATA,0)],(high,low)
            await ClockCycles(dut.clk,6000)
        device.present=False
        await p.push(0,TAG_CTRL)
        assert await drain(p,1)==[(TAG_DATA,1)]
        await ClockCycles(dut.clk,6000)
        assert await p.read(S.HOST_MAP['unit_flags'][0],1)==[0]
    finally:
        wire.stop()
    assert [fast for fast,_ in device.resets]==[False,True,True,True,True]
    dut._log.info('ONEWIRE_PRESENCE four corners, absent peer and missing-entry checks pass')

"""PS/2 malformed frames and recovery on an unmodified captured bus."""
import re

import cocotb

from chiplib import start,load,Wire,write_vcd
from kernels.ps2_checks import frame_word,FrameMonitor
from protomodels.ps2 import PS2Device
from sigrok_support import decode


@cocotb.test()
async def test_ps2_framing_and_unmodified_capture(dut):
    # Start-valid cases first: sigrok can independently decode this prefix.
    # Invalid starts can make a protocol-aware decoder resynchronize differently;
    # the raw-clock oracle covers those words and every following recovery frame.
    fault_order=(0,2,4,6,1,3,5,7)
    send=[]
    bad_start,bad_parity,bad_stop=set(),set(),set()
    for n,fault in enumerate(fault_order):
        i=len(send)
        send.extend(([0x00,0xFF,0x5A,0xA5,1,0x80,0x1C,0xF0][n],0xC3^n))
        if fault&1:bad_start.add(i)
        if fault&2:bad_parity.add(i)
        if fault&4:bad_stop.add(i)
    words=[frame_word(b,start_bad=i in bad_start,parity_bad=i in bad_parity,stop_bad=i in bad_stop)
           for i,b in enumerate(send)]
    monitor=FrameMonitor(words)
    device=PS2Device(half=1500,send=send,bad_parity=bad_parity,
                     bad_start=bad_start,bad_stop=bad_stop)
    p=await start(dut,uio=0xFF)
    await load(p,'ps2_host')

    def environment(uo,out,oe,bus):
        assert not out & oe & 3, 'PS/2 controller drove an open-drain line high'
        clk,data=bus>>1 & 1,bus & 1
        monitor.sample(clk,data)
        clk_release,data_release=device.step(clk,data)
        return {},{1:clk_release,0:data_release}

    wire=Wire(p,environment,{'clk':lambda uo,bus:bus>>1 & 1,'data':lambda uo,bus:bus & 1})
    got=[]
    try:
        for _ in range(2000):
            token=await p.pop()
            if token is not None:got.append(token)
            if len(got)==len(send) and device.frames_sent==len(send):break
        assert device.frames_sent==len(send) and len(got)==len(send)
        assert got==monitor.finish(),(got,words)
    finally:
        wire.stop()
    simulator=cocotb.SIM_NAME.replace(' ','_').replace('/','_')
    path=f'ps2_framing_{simulator}.vcd'
    write_vcd(path,wire.rec)
    text=decode(path,'ps2:clk=clk:data=data','ps2',required=True)
    decoded=[int(v,16) for v in re.findall(r'Data: ([0-9a-fA-F]{2})\b',text)]
    assert decoded[:8]==send[:8],text
    bit_text=decode(path,'ps2:clk=clk:data=data','ps2=bit',required=True)
    bits=[int(v) for v in re.findall(r': ([01])$',bit_text,re.M)]
    assert bits[:88]==[w>>bit & 1 for w in words[:8] for bit in range(11)]
    dut._log.info('PS2_FRAMING frames=%d bad_start=%d bad_parity=%d bad_stop=%d '
                  'sigrok_valid_start_prefix=8 recovery_frames=8',len(words),
                  len(bad_start),len(bad_parity),len(bad_stop))

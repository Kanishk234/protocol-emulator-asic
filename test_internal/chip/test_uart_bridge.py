"""UART multicast showcase, only chip ports, reusable on exact gates."""
import re

import cocotb
from cocotb.triggers import ClockCycles

from chiplib import start,load,Wire,write_vcd,TAGS
from protomodels import uart
from sigrok_support import decode


@cocotb.test()
async def test_uart_multicast_echo_capture_and_framing(dut):
    message=bytes([0,255,85,170,1,128,28,240,195,90])
    bad_stop={0,3,7}
    expected=[(TAGS['ERR'],b<<1) if i in bad_stop else (TAGS['DATA'],b)
              for i,b in enumerate(message)]
    for index,baud in enumerate((115200,460800)):
        cpb=50e6/baud
        wave=uart.encode(message,cpb,bad_stop=bad_stop)
        p=await start(dut,ui=1,clock=index==0)
        image=await load(p,'uart_bridge_capture',BAUD=baud)
        it=iter(wave)
        wire=Wire(p,lambda uo,out,oe,bus:({0:next(it,1)},None),
                  {'rx':lambda uo,bus:p.ui&1,'tx':lambda uo,bus:uo&1})
        got=[]
        try:
            for _ in range(2000):
                token=await p.pop()
                if token is not None:got.append(token)
                if len(got)==len(message) and wire.clocks>len(wave)+round(20*cpb):break
            assert got==expected,(baud,got)
            assert uart.decode(wire.rec['rx'],cpb)==[(b,i not in bad_stop) for i,b in enumerate(message)]
            echo=uart.decode(wire.rec['tx'],cpb)
            assert echo==[(b,True) for i,b in enumerate(message) if i not in bad_stop],(baud,echo)
            assert await p.read(0x0010,2)==[0,0], 'U0/U1: no LATE/OVERRUN or other pin flags'
        finally:
            wire.stop()
        path=f'UART_multicast_{baud}_{cocotb.SIM_NAME.replace(" ","_")}.vcd'
        write_vcd(path,wire.rec)
        text=decode(path,f'uart:rx=tx:baudrate={baud}:format=hex','uart=rx-data',required=True)
        assert [int(b,16) for b in re.findall(r'uart-\d+: ([0-9A-Fa-f]{2})\b',text)]==[
            b for i,b in enumerate(message) if i not in bad_stop]
        dut._log.info('UART_MULTICAST baud=%d host=%d DATA=7 ERR=3 echo=7 slots_L0=3 slots_L1=2',baud,len(got))

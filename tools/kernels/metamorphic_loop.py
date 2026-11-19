"""Test-only two-lane pad loopbacks and deterministic inter-frame idle insertion."""
import hashlib
import random
import re
from pathlib import Path

import tripc
from kernels import PROGRAMS
from sigrok_support import decode
from tripsim.isa import TAG_DATA,TAG_EVENT,TAG_CTRL

FIXTURES=PROGRAMS.parent/'test_internal/firmware'
PAYLOAD=bytes([0,255,1,128,85,170,60,195])


def image(protocol,rate):
    params={'BAUD':rate} if protocol=='uart' else {'PERIOD':rate}
    compiled,_=tripc.compile_file(FIXTURES/f'l4_{protocol}_loop.trw',params)
    assert set(compiled['lanes'])=={'L0','L1'}
    return compiled


class Loop:
    def __init__(self,protocol,rate,payload=PAYLOAD,seed=None,disconnected=False):
        self.protocol,self.rate,self.payload=protocol,rate,bytes(payload)
        self.initial_ui,self.initial_uio=int(protocol=='uart'),255
        self.disconnected=disconnected
        rng=random.Random(seed)
        scale=round(50e6/rate) if protocol=='uart' else rate
        self.extra_idle=[rng.randrange(1,4*scale+1) if seed is not None else 0 for _ in self.payload]
        self.guard=max(32,2*scale) if protocol=='uart' else 64
        self.frame_budget=round(20*50e6/rate)+5000 if protocol=='uart' else (rate*90+8000 if protocol=='i2c' else rate*20+5000)
        self.stops=0;self.starts=0;self.previous=(1,1)
        self.clock=0

    def commands(self,byte):
        if self.protocol=='uart':return [(byte,TAG_DATA)]
        if self.protocol=='spi':return [(0,TAG_EVENT),(byte,TAG_DATA),(1,TAG_EVENT)]
        return [(0,TAG_EVENT),(0xA0,TAG_DATA),(byte,TAG_DATA),(0,TAG_EVENT),
                (0xA1,TAG_DATA),(1,TAG_CTRL),(0x8000,TAG_EVENT)]

    def expected(self,byte):
        return [(TAG_DATA,x) for x in ([0,0,0,byte] if self.protocol=='i2c' else [byte])]

    def step(self,uo,out,oe,bus):
        self.clock+=1
        if self.protocol=='uart':return {0:1 if self.disconnected else uo&1},None
        if self.protocol=='spi':return {0:1 if self.disconnected else uo>>1&1},None
        assert not out&oe&7, 'Open-drain loop drove high'
        low=oe&~out
        scl=int(not low&2)
        sda=int(not low&(1 if self.disconnected else 5))
        target=int(not low&4) if self.disconnected else sda
        previous_scl,previous_sda=self.previous
        if previous_scl and scl and sda!=previous_sda:
            if sda:self.stops+=1
            else:self.starts+=1
        self.previous=scl,sda
        return {},{0:sda,1:scl,2:target}

    def frame_complete(self,index,received,uo):
        count=(4 if self.protocol=='i2c' else 1)*(index+1)
        if len(received)<count:return False
        if self.protocol=='spi':return bool(uo&4)
        if self.protocol=='i2c':return self.stops>=index+1
        return True

    def check(self,received):
        expected=[word for byte in self.payload for word in self.expected(byte)]
        assert received==expected,(self.protocol,received,expected)
        if self.protocol=='i2c':
            assert self.stops==len(self.payload) and self.starts==2*len(self.payload)
        return [d for t,d in received][3::4] if self.protocol=='i2c' else [d for t,d in received]


def write_vcd(path,trace):
    names=list(trace)
    assert names and len({len(trace[n]) for n in names})==1
    ids={name:chr(33+i) for i,name in enumerate(names)}
    with Path(path).open('w') as out:
        out.write('$timescale 20 ns $end\n$scope module loop $end\n')
        for name in names:out.write(f'$var wire 1 {ids[name]} {name} $end\n')
        out.write('$upscope $end\n$enddefinitions $end\n')
        previous={}
        for clock in range(len(trace[names[0]])):
            changes=[n for n in names if previous.get(n)!=trace[n][clock]]
            if changes:
                out.write(f'#{clock}\n')
                for name in changes:
                    value=trace[name][clock];assert value in (0,1)
                    out.write(f'{value}{ids[name]}\n');previous[name]=value
        out.write(f'#{len(trace[names[0]])}\n')


def audit(protocol,rate,payload,trace,path):
    write_vcd(path,trace)
    before=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    outputs={}
    if protocol=='uart':
        for line in ['tx','rx']:
            text=decode(path,f'uart:rx={line}:baudrate={rate}:format=hex','uart=rx-data',required=True)
            outputs[line]=[int(x,16) for x in re.findall(r'uart-\d+: ([0-9A-Fa-f]{2})\b',text)]
    elif protocol=='spi':
        for line in ['mosi','miso']:
            text=decode(path,'spi:clk=clk:mosi=mosi:miso=miso:cs=cs','spi='+line+'-data',required=True)
            outputs[line]=[int(x,16) for x in re.findall(r'spi-\d+: ([0-9A-Fa-f]{2})\b',text)]
    else:
        text=decode(path,'i2c:scl=scl:sda=sda','i2c',required=True)
        for direction in ['write','read']:
            outputs[direction]=[int(x,16) for x in re.findall('Data '+direction+r': ([0-9A-Fa-f]{2})\b',text)]
        assert text.count('Start repeat')==len(payload) and text.count(': Stop')==len(payload)
    assert all(values==list(payload) for values in outputs.values()),(protocol,outputs,list(payload))
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==before
    markers=frame_markers(protocol,rate,trace)
    assert len(markers)==len(payload),(protocol,markers)
    return {"capture_sha256":before,"frame_start_clocks":markers}


def run_model(protocol,rate,payload=PAYLOAD,seed=None,disconnected=False):
    from tripsim import Chip
    loop=Loop(protocol,rate,payload,seed,disconnected)
    chip=Chip(lanes=2,host_fifo_depth=1)
    chip.settle_inputs(ui=loop.initial_ui,uio=loop.initial_uio)
    tripc.load(chip,image(protocol,rate))
    names={'uart':['tx','rx'],'spi':['clk','mosi','miso','cs'],
           'i2c':['sda','scl','target_sda']}[protocol]
    trace={n:[] for n in names};received=[]
    def step():
        uo,out,oe=chip.outputs()
        ui,uio=loop.step(uo,out,oe,chip.uio_in)
        for b,v in ui.items():chip.ui_in=chip.ui_in&~(1<<b)|v<<b
        if uio is not None:
            for b,v in uio.items():chip.uio_in=chip.uio_in&~(1<<b)|v<<b
        values={'tx':uo&1,'rx':chip.ui_in&1,'clk':uo&1,'mosi':uo>>1&1,'miso':chip.ui_in&1,'cs':uo>>2&1,
                'sda':chip.uio_in&1,'scl':chip.uio_in>>1&1,'target_sda':chip.uio_in>>2&1}
        for n in names:trace[n].append(values[n])
        chip.step()
        if loop.clock%560==0 and chip.host_out:received.append(chip.host_out.popleft())
    for index,byte in enumerate(loop.payload):
        for data,tag in loop.commands(byte):chip.host_push(data,tag)
        for _ in range(loop.frame_budget):
            step()
            if loop.frame_complete(index,received,chip.outputs()[0]):break
        else:raise AssertionError(f'{protocol} loop timeout at frame{index}: {received}')
        for _ in range(loop.guard+loop.extra_idle[index]):step()
    loop.check(received)
    assert all(not unit.flags['OVERRUN'] and not unit.flags['LATE'] for unit in chip.pins)
    return trace,received,loop


def frame_markers(protocol,rate,trace):
    if protocol=='spi':return [i for i in range(1,len(trace['cs'])) if trace['cs'][i-1] and not trace['cs'][i]]
    if protocol=='i2c':
        starts=[i for i in range(1,len(trace['sda'])) if trace['sda'][i-1] and not trace['sda'][i] and trace['scl'][i-1] and trace['scl'][i]]
        assert len(starts)%2==0
        return starts[::2]
    line=trace['tx'];cpb=50e6/rate;starts=[];i=1
    while i<len(line):
        if line[i-1] and not line[i] and i+round(9.5*cpb)<len(line):
            starts.append(i);i+=round(9.5*cpb)
        else:i+=1
    return starts

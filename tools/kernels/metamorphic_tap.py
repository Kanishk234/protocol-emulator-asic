"""L4-TAP scenarios: real firmware, independent peers, a halted tap subscriber.

Shared scenario descriptions only; RTL uses chip ports and its SPI host driver.
Model execution never supplies expected pad waveforms to RTL.
"""
import hashlib
import json

import tripc
from kernels import PROGRAMS
from protomodels import uart
from protomodels.spi import SPITarget
from protomodels.i2c import I2CTarget
from tripsim.isa import TAG_CTRL, TAG_DATA, TAG_EVENT, TAG_ERR

TAP_PORT='L1.I0'
PRODUCER='L0.O1'
MESSAGE=b'tap\x00\xFF\x55\xAA'
SPI_BYTES=[0,128,255,60,90,165]
I2C_HOST=[0,0,0,1,0,0,0,0x11,0x22,0x33]


def image(protocol,rate,tap=None):
    program={'uart':'uart','spi':'spi_controller','i2c':'i2c_controller'}[protocol]
    params={'BAUD':rate} if protocol=='uart' else {'PERIOD':rate}
    source=(PROGRAMS/(program+'.trw')).read_text()
    if tap is not None:
        assert tap in ('tap','blocking')
        connection=f'connect {TAP_PORT} <- {PRODUCER}'+(' tap' if tap=='tap' else '')+'\n'
        source=source.replace('lane L0:',connection+'\nlane L0:',1)
    compiled,_=tripc.compile_text(source,params)
    return compiled


class Scenario:
    def __init__(self,protocol,rate,stretch=0,bad=False):
        self.protocol,self.rate,self.clock=protocol,rate,0
        self.initial_ui,self.initial_uio=(1 if protocol=='uart' else 0),255
        if protocol=='uart':
            self.bad={3} if bad else set()
            self.wave=uart.encode(MESSAGE,50e6/rate,bad_stop=self.bad)
            self.commands=[(b,TAG_DATA) for b in [85,170]]
            self.expected=[(TAG_ERR,b<<1) if n in self.bad else (TAG_DATA,b) for n,b in enumerate(MESSAGE)]
            self.clocks=len(self.wave)+round(20*50e6/rate)+2000
            self.mask=1
        elif protocol=='spi':
            self.peer=SPITarget(first=0xA5)
            self.commands=[(0,TAG_EVENT),*[(b,TAG_DATA) for b in SPI_BYTES],(1,TAG_EVENT)]
            self.expected=[(TAG_DATA,b) for b in [0xA5]+SPI_BYTES[:-1]]
            self.clocks=16000
            self.mask=7
        else:
            self.peer=I2CTarget(0x50,read_data=[0x11,0x22,0x33],stretch=stretch)
            S,P=(0,TAG_EVENT),(0x8000,TAG_EVENT)
            W=lambda b:(b,TAG_DATA)
            R=lambda n:(n,TAG_CTRL)
            self.commands=[S,W(0xA0),W(1),W(2),P,S,W(0xA2),P,
                           S,W(0xA0),W(5),S,W(0xA1),R(0),R(0),R(1),P]
            self.expected=[(TAG_DATA,b) for b in I2C_HOST]
            self.clocks=rate*140+8000
            self.mask=0
        self.rx=[]

    def step(self,uo,out,oe,bus):
        clock=self.clock;self.clock+=1
        if self.protocol=='uart':
            return {0:self.wave[clock] if clock<len(self.wave) else 1},None
        if self.protocol=='spi':
            return {0:self.peer.step(uo&1,uo>>1&1,uo>>2&1)},None
        scl=int(self.peer.scl and not (oe&2 and not out&2))
        sda=int(self.peer.sda and not (oe&1 and not out&1))
        self.peer.step(scl,sda)
        return {},{0:sda,1:scl}

    def finish(self,host,tx=None):
        assert host==self.expected,(self.protocol,host,self.expected)
        if self.protocol=='uart':
            if tx is not None:assert uart.decode(tx,50e6/self.rate)==[(85,True),(170,True)]
        elif self.protocol=='spi':assert self.peer.received==SPI_BYTES
        else:
            assert self.peer.received==[1,2,5]
            assert self.peer.log[-1]==('STOP',)
            assert [e[1:] for e in self.peer.log if e[0]=='ADDR']==[(0xA0,True),(0xA2,False),(0xA0,True),(0xA1,True)]


def blocking_snapshot(chip):
    # The added tap's own availability/drop count and the intentional dropped IRQ
    # are excluded; protocol pins and every pre-existing producer/port are checked.
    producers=[(n,p.valid,p.seq,p.tag,p.data,p.free(),p.loads) for n,p in chip.fabric.producers.items()]
    ports=[(n,p.avail(),p.head() if p.avail() else None,p.last_seq,p.takes,p.filtered)
           for n,p in chip.fabric.ports.items() if n!=TAP_PORT]
    return producers,ports,list(chip.host_out),[dict(u.flags) for u in chip.pins]


def compare_model(protocol,rate,stretch=0,bad=False,mode='tap'):
    from tripsim import Chip
    chips=[];scenarios=[];host=[[],[]];tx=[[],[]]
    for tap in (None,mode):
        scene=Scenario(protocol,rate,stretch,bad)
        chip=Chip(lanes=2,host_fifo_depth=1)
        chip.settle_inputs(ui=scene.initial_ui,uio=scene.initial_uio)
        tripc.load(chip,image(protocol,rate,tap))
        for data,tag in scene.commands:chip.host_push(data,tag)
        chips.append(chip);scenarios.append(scene)
    trace=hashlib.sha256()
    for clock in range(scenarios[0].clocks):
        outputs=[]
        for i,(chip,scene) in enumerate(zip(chips,scenarios)):
            uo,out,oe=chip.outputs()
            ui,uio=scene.step(uo,out,oe,chip.uio_in)
            for bit,value in ui.items():chip.ui_in=chip.ui_in&~(1<<bit)|value<<bit
            if uio is not None:
                for bit,value in uio.items():chip.uio_in=chip.uio_in&~(1<<bit)|value<<bit
            chip.step()
            if clock%560==0 and chip.host_out:host[i].append(chip.host_out.popleft())
            uo,out,oe=chip.outputs()
            outputs.append((uo&scene.mask,out,oe,chip.ui_in&1,chip.uio_in))
            tx[i].append(uo&1)
        assert outputs[0]==outputs[1],f'{protocol}: protocol pad difference at {clock}'
        assert blocking_snapshot(chips[0])==blocking_snapshot(chips[1]),f'{protocol}: blocking path difference at {clock}'
        assert host[0]==host[1],f'{protocol}: host delivery time difference at {clock}'
        trace.update(bytes([outputs[0][0],outputs[0][1],outputs[0][2]]))
    for scene,words,line in zip(scenarios,host,tx):scene.finish(words,line)
    tap=chips[1].fabric.ports[TAP_PORT]
    assert tap.en and not tap.blocking and tap.takes==0
    assert tap.dropped>0, 'Vacuous TAP test: force multiple missed tokens'
    assert all(not u.flags['OVERRUN'] and not u.flags['LATE'] for chip in chips for u in chip.pins)
    return {'protocol':protocol,'rate':rate,'stretch':stretch,'bad_stop':bad,'clocks_compared':scenarios[0].clocks,
            'tap_drops':tap.dropped,'tap_takes':tap.takes,'host_items':len(host[0]),'protocol_trace_sha256':trace.hexdigest()}

"""Legal native fast-path lane/unit permutations; routine timing audited separately."""
import re

import tripc
from kernels import PROGRAMS
from kernels.metamorphic_tap import Scenario
from protomodels.i2c import I2CController
from tripsim.isa import TAG_DATA

MAPPINGS={'baseline':(0,(0,1,2,3)),'units':(0,(2,3,0,1)),
          'lane':(1,(0,1,2,3)),'both':(1,(2,3,0,1))}
READ=[0x11,0x22,0x33]
WRITTEN=[1,2,0xA5,0xFF,0]
EXPECTED_W=[(0xA0,True),(1,True),(2,True),(0xA5,True),(0xA2,False),
            (0xA1,True),(0xA0,True),(0xFF,True),(0,True),(0xA3,False)]
EXPECTED_R=[(0x11,True),(0x22,True),(0x33,False)]


def image(protocol,rate,mapping='baseline',wrong_owner=False):
    lane,units=MAPPINGS[mapping]
    name={'uart':'uart','spi':'spi_controller','i2c':'i2c_target','i2c_controller':'i2c_controller'}[protocol]
    source=(PROGRAMS/(name+'.trw')).read_text()
    source=re.sub(r'\bU([0-3])\b',lambda m:'U'+str(units[int(m[1])]),source)
    source=re.sub(r'\bL0\b','L'+str(lane),source)
    if wrong_owner:
        # A still-legal owner selection that is not the mapped pin's transmitting unit.
        source=re.sub(r'^(own \S+ U)([0-3])$',lambda m:m[1]+str((int(m[2])+1)%4),source,count=1,flags=re.M)
    params={'BAUD':rate} if protocol=='uart' else ({'ADDR':0x50} if protocol=='i2c' else {'PERIOD':rate})
    compiled,_=tripc.compile_text(source,params)
    return compiled


class TargetScenario:
    def __init__(self,rate):
        self.protocol='i2c';self.rate=rate;self.initial_ui=0;self.initial_uio=255
        self.clocks=rate*180+8000;self.mask=0;self.clock=0
        self.commands=[(b,TAG_DATA) for b in READ+[0x44]]
        self.peer=I2CController(clocks_per_bit=rate)
        self.peer.write(0x50,[1,2,0xA5]);self.peer.write(0x51,[0x77])
        self.peer.read(0x50,3);self.peer.write(0x50,[0xFF,0]);self.peer.read(0x51,2)
        self.expected=[(TAG_DATA,b) for b in WRITTEN]

    def step(self,uo,out,oe,bus):
        self.clock+=1
        assert not out&oe&3, 'I2C drove open-drain high'
        scl=int(self.peer.scl and not (oe&2 and not out&2))
        sda=int(self.peer.sda and not (oe&1 and not out&1))
        self.peer.step(scl,sda)
        return {},{0:sda,1:scl}

    def finish(self,host,tx=None):
        assert host==self.expected,('i2c host mismatch',host,self.expected)
        assert self.peer.done(),'i2c peer timeout'
        writes=[(e[1],e[2]) for e in self.peer.log if e[0]=='W']
        reads=[(e[1],e[2]) for e in self.peer.log if e[0]=='R']
        assert writes==EXPECTED_W,('i2c ACK mismatch',writes)
        assert reads==EXPECTED_R,('i2c read mismatch',reads)


def scenario(protocol,rate):
    if protocol=='i2c':return TargetScenario(rate)
    return Scenario(protocol,rate,stretch=40 if protocol=='i2c_controller' else 0,bad=protocol=='uart')


def run_model(protocol,rate,mapping='baseline',wrong_owner=False,warmup=0,fire_period=None):
    from tripsim import Chip
    scene=scenario(protocol,rate)
    chip=Chip(lanes=2,host_fifo_depth=1,fire_period=fire_period)
    chip.settle_inputs(ui=scene.initial_ui,uio=scene.initial_uio)
    for _ in range(warmup):chip.step()
    tripc.load(chip,image(protocol,rate,mapping,wrong_owner))
    for data,tag in scene.commands:chip.host_push(data,tag)
    trace=[];got=[];deliveries=[];tx=[]
    for clock in range(scene.clocks):
        uo,out,oe=chip.outputs();ui,uio=scene.step(uo,out,oe,chip.uio_in)
        for bit,value in ui.items():chip.ui_in=chip.ui_in&~(1<<bit)|value<<bit
        if uio is not None:
            for bit,value in uio.items():chip.uio_in=chip.uio_in&~(1<<bit)|value<<bit
        chip.step()
        if clock%560==0 and chip.host_out:
            word=chip.host_out.popleft();got.append(word);deliveries.append((clock,word))
        uo,out,oe=chip.outputs();trace.append((uo&scene.mask,out,oe,chip.ui_in&1,chip.uio_in));tx.append(uo&1)
    scene.finish(got,tx)
    assert all(not u.flags['OVERRUN'] and not u.flags['LATE'] for u in chip.pins)
    return trace,deliveries

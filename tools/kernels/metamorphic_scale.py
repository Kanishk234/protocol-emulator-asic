"""D-191 timing intervals: exact programmed scaling, explicit fixed latency.

Burst boundaries come from known CLK command counts, never from gap-size guesses.
"""
import hashlib
import re
from pathlib import Path

import tripc
from kernels import PROGRAMS
from kernels.metamorphic_tap import Scenario,SPI_BYTES,MESSAGE
from kernels.metamorphic_loop import write_vcd
from sigrok_support import decode

I2C_BURSTS=[9,9,9,1,9,1,9,9,1,9,8,1,8,1,8,1,1]


def image(protocol,rate):
    name={'uart':'uart','spi':'spi_controller','i2c':'i2c_controller'}[protocol]
    return tripc.compile_file(PROGRAMS/(name+'.trw'),{'BAUD' if protocol=='uart' else 'PERIOD':rate})[0]


def scene(protocol,rate):return Scenario(protocol,rate,stretch=0,bad=False)


def edges(line,level):return [i for i in range(1,len(line)) if line[i]==level and line[i-1]!=level]


def metrics(protocol,rate,trace):
    if protocol=='uart':
        period=50_000_000//rate
        assert period*rate==50_000_000
        changed=sorted(edges(trace['tx'],0)+edges(trace['tx'],1))
        # Known sent frames 0x55/0xAA have these edge positions within each frame.
        patterns=[[0,1,2,3,4,5,6,7,8,9],[0,2,3,4,5,6,7,8]]
        assert len(changed)==sum(map(len,patterns)), 'Missing/extra UART edge'
        intervals=[];offset=0;starts=[];ends=[]
        for pattern in patterns:
            frame=changed[offset:offset+len(pattern)];offset+=len(pattern)
            assert [x-frame[0] for x in frame]==[x*period for x in pattern]
            starts.append(frame[0]);ends.append(frame[-1])
            intervals.extend(b-a for a,b in zip(frame,frame[1:]))
        return {'period':period,'programmed_intervals':intervals,'launch_clocks':starts[0],
                'excluded_interframe_edge_gap':[starts[1]-ends[0]],'fixed_recognition_clocks':0}
    period=rate;assert period%2==0
    line=trace['clk' if protocol=='spi' else 'scl']
    rising,falling=edges(line,1),edges(line,0)
    bursts=[8]*len(SPI_BYTES) if protocol=='spi' else I2C_BURSTS
    assert len(rising)==len(falling)==sum(bursts),'Missing/extra clock pulse'
    half=period//2;high=[];low=[];gaps=[];offset=0
    for count in bursts:
        r=rising[offset:offset+count];f=falling[offset:offset+count]
        if protocol=='spi':
            assert all(a<b for a,b in zip(r,f))
            high.extend(b-a for a,b in zip(r,f))
            low.extend(b-a for a,b in zip(f[:-1],r[1:]))
            if offset+count<len(rising):gaps.append(rising[offset+count]-f[-1])
        else:
            assert all(a<b for a,b in zip(f,r))
            low.extend(b-a for a,b in zip(f,r))
            high.extend(b-a for a,b in zip(r[:-1],f[1:]))
            if offset+count<len(falling):gaps.append(falling[offset+count]-r[-1])
        offset+=count
    assert all(x==half for x in low),(protocol,'low intervals',sorted(set(low)))
    if protocol=='spi':
        assert all(x==half for x in high)
        overhead=0
    else:
        # ARCHITECTURE P11/P33: synchronized stretch recognition costs up to3
        # clocks. It must be one constant across every internal high interval,
        # not a fitted correction per edge or permission to absorb host gaps.
        extra={x-half for x in high}
        assert len(extra)==1 and next(iter(extra)) in range(4),('I2C recognition',extra)
        overhead=next(iter(extra))
    programmed_high=[x-overhead for x in high]
    assert all(x==half for x in programmed_high)
    first=rising[0] if protocol=='spi' else falling[0]
    return {'period':period,'programmed_intervals':low+programmed_high,
            'fixed_recognition_clocks':overhead,'raw_high_unique':sorted(set(high)),
            'raw_low_unique':sorted(set(low)),'launch_clocks':first,
            'excluded_interburst_gaps':gaps,'bursts':bursts}


def compare(protocol,fast,slow):
    assert slow['period']==2*fast['period']
    assert slow['programmed_intervals']==[2*x for x in fast['programmed_intervals']]
    assert slow['fixed_recognition_clocks']==fast['fixed_recognition_clocks']
    if protocol=='uart':assert fast['launch_clocks']==slow['launch_clocks']
    # Launch/interburst/interframe timing is reported, never rescaled or used
    # to splice the waveform. Function and protocol oracles remain mandatory.


def audit(protocol,rate,trace,path):
    write_vcd(path,trace)
    digest=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if protocol=='uart':
        for pin,want in [('tx',[85,170]),('rx',list(MESSAGE))]:
            text=decode(path,f'uart:rx={pin}:baudrate={rate}:format=hex','uart=rx-data',required=True)
            assert [int(x,16) for x in re.findall(r'uart-\d+: ([0-9A-Fa-f]{2})\b',text)]==want
    elif protocol=='spi':
        for direction,want in [('mosi',SPI_BYTES),('miso',[0xA5]+SPI_BYTES[:-1])]:
            text=decode(path,'spi:clk=clk:mosi=mosi:miso=miso:cs=cs','spi='+direction+'-data',required=True)
            assert [int(x,16) for x in re.findall(r'spi-\d+: ([0-9A-Fa-f]{2})\b',text)]==want
    else:
        text=decode(path,'i2c:scl=scl:sda=sda','i2c',required=True)
        for direction,want in [('write',[1,2,5]),('read',[0x11,0x22,0x33])]:
            assert [int(x,16) for x in re.findall('Data '+direction+r': ([0-9A-Fa-f]{2})\b',text)]==want
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
    return digest


def run_model(protocol,rate):
    from tripsim import Chip
    s=scene(protocol,rate);c=Chip(lanes=2,host_fifo_depth=1)
    c.settle_inputs(ui=s.initial_ui,uio=s.initial_uio);tripc.load(c,image(protocol,rate))
    for data,tag in s.commands:c.host_push(data,tag)
    names={'uart':['tx','rx'],'spi':['clk','mosi','miso','cs'],'i2c':['scl','sda']}[protocol]
    trace={n:[] for n in names};got=[]
    for clock in range(s.clocks):
        uo,out,oe=c.outputs();ui,uio=s.step(uo,out,oe,c.uio_in)
        for b,v in ui.items():c.ui_in=c.ui_in&~(1<<b)|v<<b
        if uio is not None:
            assert not out&oe&3
            for b,v in uio.items():c.uio_in=c.uio_in&~(1<<b)|v<<b
        values={'tx':uo&1,'rx':c.ui_in&1,'clk':uo&1,'mosi':uo>>1&1,'miso':c.ui_in&1,'cs':uo>>2&1,'scl':c.uio_in>>1&1,'sda':c.uio_in&1}
        for n in names:trace[n].append(values[n])
        c.step()
        if clock%560==0 and c.host_out:got.append(c.host_out.popleft())
    s.finish(got,trace.get('tx'))
    assert all(not u.flags['OVERRUN'] and not u.flags['LATE'] for u in c.pins)
    return trace,metrics(protocol,rate,trace)

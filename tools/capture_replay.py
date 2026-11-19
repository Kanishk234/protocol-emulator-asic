"""Pinned real-device SR captures, exact rational resampling onto 50 MHz.

No protocol bitstream regeneration, pulse stretching, idle removal or inversion.
Only the captured digital sample levels are mapped to the simulation clock.
"""
import configparser
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'test_internal/captures/manifest.json'
CACHE=ROOT/'build/captures'
HZ=50_000_000


def digest(data):return hashlib.sha256(data).hexdigest()


def manifest():return json.loads(MANIFEST.read_text())


def fetch():
    m=manifest()
    for path,info in m['files'].items():
        target=CACHE/path
        if target.exists() and digest(target.read_bytes())==info['sha256']:continue
        url=f'https://raw.githubusercontent.com/sigrokproject/sigrok-dumps/{m["revision"]}/{path}'
        with urllib.request.urlopen(url,timeout=30) as response:data=response.read(4_000_001)
        if len(data)>4_000_000 or digest(data)!=info['sha256']:
            raise ValueError('Capture/source hash mismatch: '+path)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
    return len(m['captures'])


def verified(path):
    m=manifest()
    data=(CACHE/path).read_bytes()
    if digest(data)!=m['files'][path]['sha256']:raise ValueError('Changed capture/source: '+path)
    return data


def read_sr(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if sum(i.file_size for i in z.infolist())>16_000_000:raise ValueError('Capture exceeds size bound')
        cfg=configparser.ConfigParser()
        cfg.read_string(z.read('metadata').decode())
        dev=cfg['device 1']
        if int(dev['unitsize'])!=1:raise ValueError('Only one-byte digital samples qualified')
        rate=re.fullmatch(r'([\d.]+)\s*(Hz|kHz|MHz|GHz)',dev['samplerate'])
        if rate is None:raise ValueError('Invalid sample rate')
        hz=Fraction(rate[1])*{'Hz':1,'kHz':1000,'MHz':1000000,'GHz':1000000000}[rate[2]]
        if not 0<hz<=HZ:raise ValueError('Unsupported sample rate')
        chunks=sorted((n for n in z.namelist() if re.fullmatch(r'logic-1-\d+',n)),key=lambda n:int(n.rsplit('-',1)[1]))
        if not chunks:raise ValueError('No digital samples')
        samples=b''.join(z.read(n) for n in chunks)
        if not samples:raise ValueError('Empty digital capture')
        channels={v:int(k[5:])-1 for k,v in dev.items() if re.fullmatch(r'probe\d+',k)}
        if len(channels)!=sum(k.startswith('probe') for k in dev):raise ValueError('Duplicate channel names')
        return samples,hz,channels


class Capture:
    def __init__(self,name):
        self.name=name
        self.spec=manifest()['captures'][name]
        self.path=CACHE/self.spec['path']
        self.samples,self.hz,probes=read_sr(verified(self.spec['path']))
        self.channels={name:probes[probe] for name,probe in self.spec['channels'].items()}
        self.clocks=(len(self.samples)*HZ*self.hz.denominator+self.hz.numerator-1)//self.hz.numerator

    def levels(self,clock):
        if clock<0:raise ValueError('Negative replay time')
        sample=min(clock*self.hz.numerator//(HZ*self.hz.denominator),len(self.samples)-1)
        value=self.samples[sample]
        return {name:value>>bit&1 for name,bit in self.channels.items()}




def reference(name):
    """Decode the original SR, never a regenerated ideal protocol stream."""
    import os
    import shutil
    import subprocess
    import tripwire_spec as S
    if os.environ.get('TRIPWIRE_SKIP_SIGROK')=='1' or not shutil.which('sigrok-cli'):
        raise RuntimeError('Recorded-capture replay requires sigrok-cli')
    c=Capture(name)
    args={'uart':('uart:rx=TX:baudrate=115200:format=hex','uart=rx-data'),
          'i2c':('i2c:scl=SCL:sda=SDA','i2c'),
          'spi':('spi:clk=CLK:mosi=MOSI:cs=CS:cpol=0:cpha=0','spi=mosi-data')}
    decoder,annotations=args[name]
    text=subprocess.run(['sigrok-cli','-i',str(c.path),'-P',decoder,'-A',annotations],
                        capture_output=True,text=True,check=True).stdout
    if name in ('uart','spi'):
        data=[int(x,16) for x in re.findall(r'^(?:uart|spi)-\d+: ([0-9a-fA-F]{2})$',text,re.M)]
        if not data:raise ValueError('Vacuous decoder output')
        return [(S.TAGS['DATA'],b) for b in data],text
    tokens=[]
    pending=None
    for line in text.splitlines():
        annotation=line.partition(': ')[2]
        if annotation in ('Start','Start repeat','Stop'):
            if pending is not None:raise ValueError('Unfinished I2C byte')
            tokens.append((S.TAGS['EVENT'],0x8000 if annotation=='Stop' else 0))
        match=re.fullmatch(r'(Address|Data) (read|write): ([0-9a-fA-F]{2})',annotation)
        if match:
            if pending is not None:raise ValueError('Missing I2C ACK annotation')
            value=int(match[3],16)
            pending=(value<<1 | int(match[2]=='read')) if match[1]=='Address' else value
        if annotation in ('ACK','NACK'):
            if pending is None:raise ValueError('Unexpected I2C ACK')
            tokens.append((S.TAGS['DATA'],pending<<1 | int(annotation=='NACK')))
            pending=None
    if pending is not None or not any(t==S.TAGS['DATA'] for t,d in tokens):
        raise ValueError('Incomplete/vacuous I2C decoder output')
    return tokens,text


def normalized(name,tokens):
    import tripwire_spec as S
    if name=='spi':return [(t,d) for t,d in tokens if t==S.TAGS['DATA']]
    return [(t,d&0x8000 if t==S.TAGS['EVENT'] else d) for t,d in tokens]


def pads(name,levels):
    """Return ui protocol bits and uio byte; host pins are left to the driver."""
    if name=='uart':return {0:levels['rx']},0xFF
    if name=='spi':return {0:levels['mosi'],1:levels['clk'],2:levels['cs']},0xFF
    return {},0xFC|levels['sda']|levels['scl']<<1


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch',action='store_true',required=True)
    parser.parse_args()
    print('Verified real-device captures:',fetch())


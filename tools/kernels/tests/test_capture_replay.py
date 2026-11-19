"""Real-device SR samples replayed at their original rate on unchanged receivers."""
import hashlib
import json

import pytest
import tripc
from capture_replay import Capture,reference,normalized,pads
from kernels import PROGRAMS
from tripsim import Chip
from host import HM
import tripwire_spec as S


@pytest.mark.parametrize('name',['uart','i2c','spi'])
def test_original_recording_matches_independent_decoder(name):
    capture=Capture(name)
    expected,text=reference(name)
    chip=Chip(lanes=2,host_fifo_depth=1)
    first_ui,first_uio=pads(name,capture.levels(0))
    chip.settle_inputs(ui=sum(v<<b for b,v in first_ui.items()),uio=first_uio)
    image,_=tripc.compile_file(PROGRAMS/(capture.spec['program']+'.trw'),capture.spec['params'])
    tripc.load(chip,image)
    got=[]
    for clock in range(capture.clocks+3000):
        ui,uio=pads(name,capture.levels(clock))
        chip.ui_in=sum(v<<b for b,v in ui.items())
        chip.uio_in=uio
        chip.step()
        if chip.host_out:got.append(chip.host_out.popleft())
        assert chip.outputs()[2]==0, 'Recorded bus replay must be passive'
    if name=='spi':
        assert image['sram'][32:96]==[0xFFFF]*64
        words=[chip.host_read(HM['sram']+32+i) for i in range(64)]
        assert words[len(expected):]==[0xFFFF]*(64-len(expected))
        got=[(S.TAGS['DATA'],w) for w in words[:len(expected)]]
    assert normalized(name,got)==expected,(name,got,expected)
    unit=1 if name=='uart' else 0
    assert not chip.pins[unit].flags['OVERRUN']
    print('REAL_CAPTURE '+json.dumps({'name':name,'samples':len(capture.samples),
          'sample_rate':str(capture.hz),'clocks':capture.clocks,'host_tokens':len(got),
          'decoded_items':len(expected),'source_sha256':hashlib.sha256(capture.path.read_bytes()).hexdigest(),
          'decode_sha256':hashlib.sha256(text.encode()).hexdigest()},sort_keys=True))

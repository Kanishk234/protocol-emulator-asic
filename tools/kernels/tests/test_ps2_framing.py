"""Independent malformed frames, classification and following-frame recovery."""
import re

import pytest
import tripc
from kernels import PROGRAMS
from kernels.ps2_checks import frame_word, FrameMonitor
from protomodels.ps2 import PS2Device
from sigrok_support import decode
from tripsim import Chip
from tripsim.vcd import VcdRecorder


def run(send, *, half=1500, bad_start=(), bad_parity=(), bad_stop=(), vcd=None, relax_framing=False):
    chip=Chip(lanes=2)
    chip.settle_inputs(uio=0xFF)
    image,_=tripc.compile_file(PROGRAMS/'ps2_host.trw')
    tripc.load(chip,image)
    if relax_framing:
        chip.lanes[0].k[:2]=[0,0]  # scratch negative control, not loaded firmware
    peer=PS2Device(half,send,bad_parity,bad_start,bad_stop)
    words=[frame_word(byte,start_bad=i in bad_start,parity_bad=i in bad_parity,stop_bad=i in bad_stop)
           for i,byte in enumerate(send)]
    monitor=FrameMonitor(words)
    recorder=None
    if vcd:
        recorder=VcdRecorder({'clk':lambda c:c.uio_in>>1 & 1,'data':lambda c:c.uio_in & 1})
        chip.observers.append(recorder)
    for _ in range(len(send)*27*half+3000):
        _,out,oe=chip.outputs()
        assert not out & oe & 3, 'PS/2 open-drain line driven high'
        clk=int(peer.clk and not (oe & 2 and not out & 2))
        data=int(peer.data and not (oe & 1 and not out & 1))
        monitor.sample(clk,data)
        chip.uio_in=0xFC | clk<<1 | data
        chip.step()
        peer.step(clk,data)
    assert peer.frames_sent==len(send)
    expected=monitor.finish()
    assert list(chip.host_out)==expected, 'PS/2 framing classification mismatch'
    assert not any(p.flags['OVERRUN'] for p in chip.pins)
    if recorder:recorder.write(vcd)
    return words,expected


@pytest.mark.parametrize('half',[1500,2000,2500])
@pytest.mark.parametrize('byte',[0,255,0x5A,0xA5,1,0x80])
@pytest.mark.parametrize('faults',range(8))
def test_all_framing_parity_combinations_recover(half,byte,faults):
    # The second frame must remain valid after every first-frame defect.
    run([byte,byte^0xFF],half=half,
        bad_start={0} if faults&1 else set(),
        bad_parity={0} if faults&2 else set(),
        bad_stop={0} if faults&4 else set())


def test_relaxed_start_stop_mask_is_detected():
    # Two flipped framing bits preserve parity, so the framing check itself
    # must reject this word; a parity-only test would miss the regression.
    with pytest.raises(AssertionError,match='framing classification'):
        run([0x5A,0xA5],bad_start={0},bad_stop={0},relax_framing=True)


def test_unmodified_capture_parity_and_stop_bits_match_sigrok(tmp_path):
    send=[0x1C,0,0xFF,0x5A,0xA5,0x80,1,0xF0]
    path=tmp_path/'raw_ps2.vcd'
    words,_=run(send,bad_parity={1,3},bad_stop={2,3},vcd=path)
    text=decode(path,'ps2:clk=clk:data=data','ps2',required=True)
    assert [int(b,16) for b in re.findall(r'Data: ([0-9a-fA-F]{2})\b',text)]==send,text
    assert text.count('Parity error')==2,text
    bits=decode(path,'ps2:clk=clk:data=data','ps2=bit',required=True)
    actual=[int(b) for b in re.findall(r': ([01])$',bits,re.M)]
    assert actual==[word>>bit & 1 for word in words for bit in range(11)]

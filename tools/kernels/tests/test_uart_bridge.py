"""Finite wire-to-multicast workloads with a one-token host consumer."""
import re

import pytest
import tripc
from kernels import PROGRAMS
from protomodels import uart
from tripsim import Chip
from tripsim.isa import TAG_DATA, TAG_ERR
from tripsim.vcd import VcdRecorder
from sigrok_support import decode


def tokens(message, bad_stop):
    return [(TAG_ERR,(b<<1)) if i in bad_stop else (TAG_DATA,b)
            for i,b in enumerate(message)]


def run(message,baud,bad_stop=(),*,drain_period=560,first_drain=0,disconnect=False):
    chip=Chip(lanes=2,host_fifo_depth=1)
    chip.settle_inputs(ui=1)
    image,_=tripc.compile_file(PROGRAMS/'uart_bridge_capture.trw',{'BAUD':baud})
    if disconnect:image['connect']=[c for c in image['connect'] if c[0]!='L1.I0']
    tripc.load(chip,image)
    cpb=50e6/baud
    wave=uart.encode(message,cpb,bad_stop=bad_stop)
    rec=VcdRecorder({'rx':lambda c:c.ui_in&1,'tx':lambda c:c.outputs()[0]&1})
    chip.observers.append(rec)
    tx,got=[],[]
    for i in range(len(wave)+round(20*cpb)+4*drain_period):
        chip.ui_in=wave[i] if i<len(wave) else 1
        chip.step()
        tx.append(chip.outputs()[0]&1)
        if i>=first_drain and i%drain_period==0 and chip.host_out:
            got.append(chip.host_out.popleft())
    return chip,image,rec,got,uart.decode(tx,cpb)


def check(message,bad_stop,got,echo):
    assert got==tokens(message,bad_stop)
    assert echo==[(b,True) for i,b in enumerate(message) if i not in bad_stop]


@pytest.mark.parametrize('baud',[115200,460800])
@pytest.mark.parametrize('bad_stop',[(),(0,3,7)])
def test_multicast_and_framing_recovery(baud,bad_stop,tmp_path):
    message=bytes([0,255,85,170,1,128,28,240,195,90])
    chip,image,rec,got,echo=run(message,baud,bad_stop)
    check(message,bad_stop,got,echo)
    assert not chip.pins[1].flags['OVERRUN']
    assert not chip.pins[0].flags['LATE']
    path=tmp_path/'uart_multicast.vcd'
    rec.write(path)
    out=decode(path,f'uart:rx=tx:baudrate={baud}:format=hex','uart=rx-data',required=True)
    assert [int(b,16) for b in re.findall(r'uart-\d+: ([0-9a-fA-F]{2})\b',out)]==[
        b for i,b in enumerate(message) if i not in bad_stop]


def test_all_byte_values_with_hardware_sized_host_queue():
    message=bytes(range(256))
    chip,_,_,got,echo=run(message,460800)
    check(message,(),got,echo)
    assert not chip.pins[1].flags['OVERRUN']


def test_delayed_host_service_with_one_isolated_frame():
    chip,_,_,got,echo=run(b'\xA5',460800,first_drain=2500)
    check(b'\xA5',(),got,echo)
    assert not chip.pins[1].flags['OVERRUN']


def test_sustained_input_without_host_service_exposes_overrun():
    chip,_,_,got,_=run(bytes(range(32)),460800,first_drain=100000)
    assert chip.pins[1].flags['OVERRUN'], 'A blocking capture is not unbounded buffering'
    assert got==[]


def test_disconnected_multicast_branch_is_detected():
    _,_,_,got,echo=run(b'\x55\xA5',460800,disconnect=True)
    with pytest.raises(AssertionError):check(b'\x55\xA5',(),got,echo)

"""Existing controller primitives: standard entry, overdrive reset/read, exit."""
import pytest
import re
import shutil
import subprocess
import tripc
from kernels import PROGRAMS
from protomodels.onewire import US
from protomodels.onewire_overdrive import OverdriveROMDevice
from tripsim import Chip
from tripsim.isa import TAG_CTRL, TAG_DATA
from tripsim.vcd import VcdRecorder


def load(chip, fast):
    chip.halt()
    lane,unit=chip.lanes[0],chip.pins[0]
    assert not lane.rb and lane.exec_latch is None
    assert not unit.actions and unit.clk is None and not unit.linked_bits
    image,_=tripc.compile_file(PROGRAMS/'onewire_master.trw',{'OVERDRIVE':int(fast)})
    tripc.load(chip,image)
    return image


def run(chip,device,clocks,observer=None):
    for _ in range(clocks):
        _,out,oe=chip.outputs()
        assert not out & oe & 1, 'Controller drove the open-drain bus high'
        bus=int(device.drive and not (oe & 1 and not out & 1))
        if observer is not None:observer(chip.cycle,bool(oe & 1 and not out & 1))
        chip.uio_in=0xFE|bus
        chip.step()
        device.step(bus)
    assert not chip.pins[0].flags['OVERRUN']


def enter(chip,device):
    load(chip,False)
    chip.host_push(0,TAG_CTRL)
    chip.host_push(0x3C)
    run(chip,device,1800*US)
    assert list(chip.host_out)==[(TAG_DATA,0)]
    chip.host_out.clear()
    assert device.overdrive and device.entries==1
    assert device.history==[(False,0x3C)]


def read_rom(chip,device,fast,*,sample_override=None):
    load(chip,fast)
    if sample_override is not None:chip.lanes[0].k[2]=sample_override
    chip.host_push(0,TAG_CTRL)
    chip.host_push(0x33)
    for _ in range(8):chip.host_push(1,TAG_CTRL)
    run(chip,device,(1100 if fast else 6500)*US)
    assert list(chip.host_out)==[(TAG_DATA,0),*[(TAG_DATA,b) for b in device.rom]], 'ROM readback mismatch'
    chip.host_out.clear()
    assert device.received==[0x33]


def test_default_master_is_bit_identical_to_legacy_standard_program():
    old,_=tripc.compile_file(PROGRAMS/'onewire.trw')
    new,_=tripc.compile_file(PROGRAMS/'onewire_master.trw')
    assert {k:v for k,v in old.items() if k not in ('program','params')} == {
        k:v for k,v in new.items() if k not in ('program','params')}


def test_standard_entry_overdrive_read_and_standard_exit(tmp_path):
    chip=Chip(lanes=2)
    chip.settle_inputs(uio=0xFF)
    device=OverdriveROMDevice()
    recorder=VcdRecorder({'dq':lambda c:c.uio_in & 1})
    chip.observers.append(recorder)
    enter(chip,device)
    read_rom(chip,device,True)
    assert device.overdrive and [mode for mode,_ in device.resets]==[False,True]
    read_rom(chip,device,False)
    assert not device.overdrive and [mode for mode,_ in device.resets]==[False,True,False]
    assert shutil.which('sigrok-cli'), 'Required independent 1-Wire decoder unavailable'
    path=tmp_path/'onewire_speeds.vcd'
    recorder.write(path)
    decoded=subprocess.run(['sigrok-cli','-i',str(path),'-I','vcd',
                            '-P','onewire_link:owr=dq,onewire_network','-A','onewire_network'],
                           capture_output=True,text=True,check=True).stdout
    assert re.search(r'overdrive.*skip',decoded,re.I),decoded
    assert decoded.count('Read ROM')==2,decoded
    roms=re.findall(r'ROM: 0x([0-9a-fA-F]{16})',decoded)
    assert [int(r,16) for r in roms]==[int.from_bytes(bytes(device.rom),'little')]*2,decoded


def test_fast_reset_without_entry_does_not_invent_presence():
    chip=Chip(lanes=2)
    chip.settle_inputs(uio=0xFF)
    device=OverdriveROMDevice()
    load(chip,True)
    chip.host_push(0,TAG_CTRL)
    run(chip,device,300*US)
    assert list(chip.host_out)==[(TAG_DATA,1)]
    assert not device.resets and not device.overdrive


def test_disconnected_peer_releases_a_previously_low_output():
    device=OverdriveROMDevice()
    device.drive=0
    device.present=False
    assert device.step(0)==device.drive==1


@pytest.mark.parametrize('high,low',[(2,8),(2,24),(6,8),(6,24)])
def test_overdrive_presence_timing_corners(high,low):
    chip=Chip(lanes=2)
    chip.settle_inputs(uio=0xFF)
    device=OverdriveROMDevice()
    enter(chip,device)
    device.presence_high,device.presence_low=high*US,low*US
    read_rom(chip,device,True)


@pytest.mark.parametrize('fast',[False,True])
def test_absent_peer_reports_no_presence(fast):
    chip=Chip(lanes=2)
    chip.settle_inputs(uio=0xFF)
    device=OverdriveROMDevice(present=False)
    load(chip,fast)
    chip.host_push(0,TAG_CTRL)
    run(chip,device,(300 if fast else 1100)*US)
    assert list(chip.host_out)==[(TAG_DATA,1)]


def test_late_overdrive_sample_is_rejected_by_independent_peer():
    chip=Chip(lanes=2)
    chip.settle_inputs(uio=0xFF)
    device=OverdriveROMDevice()
    enter(chip,device)
    # One extra 0.5 us tick moves sampling beyond the peer's 2 us endpoint.
    with pytest.raises(AssertionError,match='ROM readback mismatch'):
        read_rom(chip,device,True,sample_override=0x8003)


def test_overdrive_write_slots_and_pre_reset_recovery():
    chip=Chip(lanes=2)
    chip.settle_inputs(uio=0xFF)
    device=OverdriveROMDevice()
    enter(chip,device)
    load(chip,True)
    widths=[]
    state={'start':None}
    def observe(clock,low):
        if low and state['start'] is None:state['start']=clock
        if not low and state['start'] is not None:
            widths.append((state['start'],clock-state['start']))
            state['start']=None
    chip.host_push(0xA5)
    run(chip,device,150*US,observe)
    assert len(widths)==8
    for bit,(_,width) in enumerate(widths):
        if 0xA5 >> bit & 1:assert 1*US <= width <= 2*US
        else:assert 6*US <= width <= 15.5*US
    for (start,width),(following,_) in zip(widths,widths[1:]):
        assert following-start>=8*US and following-start-width>=2*US
    widths.clear()
    chip.host_push(0x00)
    chip.host_push(0,TAG_CTRL)
    run(chip,device,300*US,observe)
    assert len(widths)==9 and widths[-1][1]==70*US
    assert widths[-1][0]-sum(widths[-2])>=5*US
    assert list(chip.host_out)==[(TAG_DATA,0)]

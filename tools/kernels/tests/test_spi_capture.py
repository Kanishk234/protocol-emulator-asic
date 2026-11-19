"""Bounded SRAM capture and the live-host counterexample, separate from real replay."""
import pytest
import tripc
from capture_replay import Capture,pads,reference
from kernels import PROGRAMS
from protomodels.spi import SPIController
from tripsim import Chip


@pytest.mark.parametrize('count',[0,1,64,128])
def test_capture_capacity_never_wraps_or_overwrites_code(count):
    chip=Chip(lanes=2,host_fifo_depth=1)
    chip.settle_inputs(ui=4,uio=255)
    image,_=tripc.compile_file(PROGRAMS/'spi_capture.trw')
    tripc.load(chip,image)
    controller=SPIController(half=25)
    controller.transfer(bytes(range(count)))
    for _ in range(max(1,count)*400+2000):
        sck,mosi,cs=controller.step(1)
        chip.ui_in=mosi|sck<<1|cs<<2
        chip.step()
        assert chip.outputs()[2]==0
    assert controller.done()
    stored=min(count,64)
    assert chip.sram.mem[32:96]==list(range(stored))+[0xFFFF]*(64-stored)
    assert chip.sram.mem[:32]==image['sram'][:32]
    assert chip.sram.mem[96:len(image['sram'])]==image['sram'][96:]
    assert bool(chip.pins[0].flags['OVERRUN'])==(count>64)


@pytest.mark.parametrize('drain_period',[1,1120])
def test_original_live_forwarder_needs_a_host_service_contract(drain_period):
    capture=Capture('spi')
    expected,_=reference('spi')
    text='''program original_live
pin U0: pin_a=ui0 pin_b=ui1 pin_c=ui2 c_active=0 order=msb idle=1 rxmode=linked_rx rx_edge=rise rx_nbits=8 ev_pin=c ev_edge=both
connect L0.I0 <- U0.rx accept=DATA
connect HOST_OUT <- L0.O1
lane L0:
    slot: do MOV O1 <- I0, deq, keep
'''
    chip=Chip(lanes=2,host_fifo_depth=1)
    ui,uio=pads('spi',capture.levels(0))
    chip.settle_inputs(ui=sum(v<<b for b,v in ui.items()),uio=uio)
    image,_=tripc.compile_text(text)
    tripc.load(chip,image)
    got=[]
    for clock in range(capture.clocks+5000):
        ui,uio=pads('spi',capture.levels(clock))
        chip.ui_in=sum(v<<b for b,v in ui.items());chip.uio_in=uio
        chip.step()
        if clock%drain_period==0 and chip.host_out:got.append(chip.host_out.popleft())
    if drain_period==1:
        assert got==expected and not chip.pins[0].flags['OVERRUN']
    else:
        assert got==[expected[i] for i in (0,1,2,4)]
        assert chip.pins[0].flags['OVERRUN']

"""SPI memory firmware against a transaction oracle independent of its ISA."""
import pytest
import re
import shutil
import subprocess
import tripc
from kernels import PROGRAMS
from protomodels.spi import SPIController
from protomodels.spi_flash import read_request, response, FlashWireMonitor
from tripsim import Chip
from tripsim.vcd import VcdRecorder


MEMORY = bytes(((73 * i + 19) ^ (i >> 1)) & 255 for i in range(256))


def run(transfers, half=50, *, gap=128, tcss=8, image=None, vcd=None, phase=0):
    if image is None:
        image, _ = tripc.compile_file(PROGRAMS / 'spi_target_flash.trw')
    assert bytes(image['sram'][32:288]) == MEMORY
    assert len(image['lanes']['L0']['slots']) == 12
    chip = Chip(lanes=2)
    chip.cycle = phase  # vary the SRAM rotation relative to the same wire waveform
    chip.settle_inputs(ui=4)
    tripc.load(chip, image)
    controller = SPIController(half, gap=gap, tcss=tcss)
    monitor = FlashWireMonitor(MEMORY, transfers)
    if vcd:
        recorder = VcdRecorder({'sck':lambda c:c.ui_in >> 1 & 1,
                                'mosi':lambda c:c.ui_in & 1,'cs':lambda c:c.ui_in >> 2 & 1,
                                'miso':lambda c:c.outputs()[1] & 1 if c.outputs()[2] & 1 else 1})
        chip.observers.append(recorder)
    for request, bits in transfers:
        controller.transfer(request, bits)
    oe_delay = 0
    longest = 0
    clocks = sum((len(req)*8 if bits is None else bits)*2*half + gap + tcss + 2*half
                 for req,bits in transfers) + gap + 1000
    for _ in range(clocks):
        _, outputs, enables = chip.outputs()
        oe_delay = oe_delay + 1 if controller.cs and enables & 1 else 0
        longest = max(longest, oe_delay)
        miso = outputs & 1 if enables & 1 else 1
        sck, mosi, cs = controller.step(miso)
        monitor.sample(chip.cycle, sck, mosi, cs, miso, enables & 1)
        chip.ui_in = mosi | sck << 1 | cs << 2
        chip.step()
        if controller.done():
            break
    assert controller.done(), 'SPI memory waveform timed out'
    chip.run_for(128)
    assert longest <= 3, longest
    assert not any(p.flags['OVERRUN'] for p in chip.pins)
    assert not any(p.stats['bad_tokens'] for p in chip.pins)
    assert len(controller.results) == len(transfers)
    for (request, bits), actual in zip(transfers, controller.results):
        complete = len(request) if bits is None else bits // 8
        expected = response(MEMORY, request[:complete])
        assert len(actual) == complete
        assert all(e is None or e == a for e,a in zip(expected,actual)), (request, actual, expected)
    summary = monitor.finish()
    if vcd:
        recorder.write(vcd)
    print('SPI_FLASH', half, summary)
    return image, controller


@pytest.mark.parametrize('half', [50, 75, 100])
@pytest.mark.parametrize('command', [0x03, 0x0B])
def test_read_addresses_wrap_and_dummy(command, half):
    transfers = [(read_request(command, address, 12, dummy=dummy), None)
                 for address,dummy in [(0,0), (1,0xFF), (0xFE,0xA5), (0x12347F,0x55)]]
    run(transfers, half)


@pytest.mark.parametrize('bits', range(1, 49))
@pytest.mark.parametrize('command', [0x03, 0x0B])
def test_abort_then_new_command(command, bits):
    prefix = read_request(command, 0xFC, 8, dummy=0xA5)
    after = read_request(0x0B if command == 0x03 else 0x03, 0x31, 8, dummy=0x5A)
    run([(prefix,bits), (after,None)])


def test_unsupported_command_is_drained_until_cs():
    garbage = bytes([0x02, 0x03, 0, 0, 0, 0x0B, 0, 0, 0, 0] * 2)
    run([(garbage,None), (read_request(0x03,0x80,16),None)])


@pytest.mark.parametrize('phase', range(4))
def test_memory_service_rotation_alignments(phase):
    run([(read_request(3,0xFE,12),None),
         (read_request(11,1,12,dummy=0xFF),None)],
        phase=phase)


def test_transaction_oracle_has_eight_fast_dummy_clocks():
    memory = bytes([0x12,0xA5,0x7E])
    assert response(memory,bytes([3,0,0,1,0,0,0])) == [None]*4+[0xA5,0x7E,0x12]
    assert response(memory,bytes([11,0,0,1,0xFF,0,0,0])) == [None]*5+[0xA5,0x7E,0x12]
    assert response(memory,bytes([2,3,0,0,0,0])) == [None]*6


def test_first_reply_requires_wait_for_header_falling_edge():
    image, _ = tripc.compile_file(PROGRAMS / 'spi_target_flash.trw')
    image['lanes']['L0']['k'][3] = 0x5000  # replace WAIT with immediate SYNC, test instance only
    with pytest.raises(AssertionError, match='data mismatch'):
        run([(read_request(3,0,8),None)], image=image)


def test_spi_memory_sigrok(tmp_path):
    assert shutil.which('sigrok-cli'), 'Required SPI decoder is unavailable'
    transfers=[(read_request(3,0xFC,8),None),(read_request(11,0x123401,8,dummy=0xA5),None)]
    path=tmp_path/'spi_memory.vcd'
    _,ctrl=run(transfers,vcd=path)
    for cls,want in [('mosi-data',[b for req,_ in transfers for b in req]),
                     ('miso-data',[b for row in ctrl.results for b in row])]:
        text=subprocess.run(['sigrok-cli','-i',str(path),'-I','vcd',
                             '-P','spi:clk=sck:mosi=mosi:miso=miso:cs=cs','-A',f'spi={cls}'],
                            capture_output=True,text=True,check=True).stdout
        actual=[int(h,16) for h in re.findall(r'spi-\d+: ([0-9A-F]{2})\b',text)]
        assert actual==want,(cls,actual,want)

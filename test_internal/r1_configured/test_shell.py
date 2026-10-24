"""Candidate primary workload through production management SPI, top-level ports only."""
import json
import os
import sys
from pathlib import Path

import cocotb
from cocotb.triggers import RisingEdge, Timer, with_timeout
from cocotb.utils import get_sim_time

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'test'))
from compile.bitfile import BitFile
from test_loaded import capture_configuration
from warp_host import reset, expect, parked, bit
from host.protocol import (State, ErrorCode, Op, tx_simple, tx_load_begin,
                           tx_load_data, tx_load_end, crc32_words, tx_ch_write,
                           tx_ch_read, parse_channel_read, tx_read_id, parse_read_id)
from host.protocol import load_transactions


async def cycle(d,n=1):
    for _ in range(n):
        await RisingEdge(d.clk)
        await Timer(1,unit='ns')


@cocotb.test()
async def shell_loaded_primary(d):
    host=await reset(d)
    host.set_fab_in(3)  # RX idle and SPI MISO high, including while loading.
    assert parse_read_id(await host.xfer(tx_read_id()))==(True,0xfe)
    await expect(host,State.UNCONFIGURED)
    assert parked(d)
    words=BitFile.load(os.environ['R1_IMAGE']).words
    async def load_image():
        for index,transaction in enumerate(load_transactions(words,5,0xfe)):
            await host.xfer(transaction)
            if index%32==0:d._log.info('Image load transaction %d complete',index)

    await host.xfer(tx_load_begin(len(words),arch_version=3))
    await expect(host,State.ERROR,ErrorCode.WRONG_ARCH)
    # READ_STATUS above acknowledges the sticky error; refused RUN sets BAD_COMMAND.
    await host.xfer(tx_simple(Op.RUN))
    await expect(host,State.ERROR,ErrorCode.BAD_COMMAND)
    assert parked(d)

    # Correct framing and length, deliberately corrupt CRC, then prove RUN is refused.
    probe=[0xfab0fab1,0]
    await host.xfer(tx_load_begin(len(probe),arch_version=0xfe))
    await host.xfer(tx_load_data(probe))
    await host.xfer(tx_load_end(crc32_words(probe)^1))
    await expect(host,State.ERROR,ErrorCode.CRC)
    await host.xfer(tx_simple(Op.RUN))
    await expect(host,State.ERROR,ErrorCode.BAD_COMMAND)
    assert parked(d)

    await load_image()
    await expect(host,State.LOADED)
    assert parked(d)
    d._log.info('Candidate image loaded through management SPI; rejection checks passed')
    first_configuration=None
    if os.environ.get('R1_CFG_SNAPSHOT'):
        first_configuration=capture_configuration(d,os.environ['R1_CFG_SNAPSHOT']+'.first.json')
    await host.xfer(tx_simple(Op.RUN))
    await expect(host,State.RUNNING)
    await cycle(d,10)
    div=int(os.environ['R1_DIV']);half=int(os.environ['R1_HALF'])
    activity={}

    async def uart_tx():
        for _ in range(20000):
            if bit(d.uo_out,2)==0:break
            await cycle(d)
        else:raise AssertionError('No UART TX after shell channel writes')
        start=get_sim_time(unit='ns')
        await cycle(d,div+div//2)
        value=0
        for index in range(8):
            value|=bit(d.uo_out,2)<<index
            await cycle(d,div)
        assert value==0xa5 and bit(d.uo_out,2)==1
        activity['uart_tx']=(start,get_sim_time(unit='ns'))

    async def uart_rx():
        await cycle(d,12)
        start=get_sim_time(unit='ns')
        for level in [0]+[(0x69>>index)&1 for index in range(8)]+[1]:
            host.set_fab_in(2|level)
            await cycle(d,div)
        activity['uart_rx']=(start,get_sim_time(unit='ns'))

    async def spi_peer(expected=0x3c,record=True):
        for _ in range(20000):
            if not bit(d.uo_out,5):break
            await cycle(d)
        else:raise AssertionError('No SPI select after shell channel writes')
        start=get_sim_time(unit='ns')
        value=0;count=0;elapsed=0;last_edge=None;previous=bit(d.uo_out,3)
        while not bit(d.uo_out,5):
            now=bit(d.uo_out,3)
            if now and not previous:
                if last_edge is not None:assert elapsed-last_edge==2*half
                last_edge=elapsed;count+=1;value=(value<<1)|bit(d.uo_out,4)
            previous=now;await cycle(d);elapsed+=1
        assert count==8 and value==expected
        if record:activity['spi']=(start,get_sim_time(unit='ns'))

    tasks=[cocotb.start_soon(task()) for task in (uart_tx,uart_rx,spi_peer)]
    for value in (0,0xa5,3,0x3c):
        await host.xfer(tx_ch_write(value))
    # Withhold CH_READ until both producers complete: the two-entry receive FIFO
    # fills, so the later response must survive fabric-side backpressure.
    for task in tasks:await with_timeout(task,1000,'us')
    d._log.info('Primary pin traffic complete; draining shell response FIFO')
    overlap=min(end for start,end in activity.values())-max(start for start,end in activity.values())
    assert len(activity)==3 and overlap>0,activity
    received=[]
    for _ in range(100):
        status,value=parse_channel_read(await host.xfer(tx_ch_read()))
        assert not status.ch_overflow and not status.error_pending
        if value is not None:received.append(value)
        if len(received)==4:break
    assert len(received)==4
    assert received[0]!=received[2] and {received[0]:received[1],received[2]:received[3]}=={0:0x69,1:0xff}
    await expect(host,State.RUNNING)
    d._log.info('Primary response packets correct; testing USER_RESET')
    await host.xfer(tx_simple(Op.USER_RESET))
    await expect(host,State.RUNNING)
    await cycle(d,10)
    assert bit(d.uo_out,2)==1 and bit(d.uo_out,5)==1
    d._log.info('USER_RESET completed; testing STOP/restart')
    await host.xfer(tx_simple(Op.STOP))
    await expect(host,State.LOADED)
    assert parked(d)
    await host.xfer(tx_simple(Op.RUN))
    await expect(host,State.RUNNING)
    await cycle(d,10)
    assert bit(d.uo_out,2)==1 and bit(d.uo_out,5)==1
    await host.xfer(tx_simple(Op.STOP))
    await expect(host,State.LOADED)
    assert parked(d)
    # A second full load checks recovery/reload without chip reset.
    if os.environ.get('R1_SHELL_RESTART_ONLY')!='1':
        d._log.info('STOP/restart complete; reloading image')
        await load_image()
        await expect(host,State.LOADED)
        assert parked(d)
        if first_configuration is not None:
            assert capture_configuration(d,os.environ['R1_CFG_SNAPSHOT'])==first_configuration, 'Native configuration changed across same-image reload'
            d._log.info('All observed native configuration values match after reload')
    elif first_configuration is not None:
        capture_configuration(d,os.environ['R1_CFG_SNAPSHOT'])
    await host.xfer(tx_simple(Op.RUN))
    await expect(host,State.RUNNING)
    await cycle(d,10)
    peer=cocotb.start_soon(spi_peer(0x5a,False))
    d._log.info('Reload complete; starting second SPI transfer')
    for value in (3,0x5a):
        await host.xfer(tx_ch_write(value))
        d._log.info('Postreload channel byte %02x sent',value)
    await with_timeout(peer,1000,'us')
    reloaded=[]
    for _ in range(100):
        status,value=parse_channel_read(await host.xfer(tx_ch_read()))
        assert not status.ch_overflow and not status.error_pending
        if value is not None:reloaded.append(value)
        if len(reloaded)==2:break
    assert reloaded==[1,0xff]
    await host.xfer(tx_simple(Op.STOP))
    await expect(host,State.LOADED)
    assert parked(d)
    Path(os.environ['R1_ACTIVITY']).write_text(json.dumps(dict(windows_ns=activity,overlap_ns=overlap),indent=2,sort_keys=True)+'\n')
    d._log.info('Real management SPI primary passed; simultaneous activity %s ns',overlap)

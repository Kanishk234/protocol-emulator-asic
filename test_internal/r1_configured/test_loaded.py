"""Configured-fabric concurrent UART/SPI smoke; frame-FSM loading, no SPI shell."""
import os
import json
from pathlib import Path
import cocotb
from cocotb.handle import HierarchyObject
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge,Timer,with_timeout
from cocotb.utils import get_sim_time
from compile.bitfile import BitFile

async def cycle(d,n=1):
    for _ in range(n):
        await RisingEdge(d.clk)
        await Timer(1,unit='ns')

async def put(d,value):
    d.h_wdata.value=value;d.h_wvalid.value=1
    for _ in range(20000):
        ready=int(d.h_wready.value)
        await cycle(d)
        if ready:
            d.h_wvalid.value=0
            return
    raise AssertionError('configured host-write handshake timeout')

async def get(d):
    d.h_rready.value=0
    for _ in range(20000):
        if int(d.h_rvalid.value):
            value=int(d.h_rdata.value)
            await cycle(d,5)
            assert int(d.h_rvalid.value) and int(d.h_rdata.value)==value
            d.h_rready.value=1;await cycle(d);d.h_rready.value=0
            return value
        await cycle(d)
    raise AssertionError('configured host-read handshake timeout')


def capture_configuration(d,path):
    tiles={}
    for tile in d.fabric:
        if not isinstance(tile,HierarchyObject) or not tile._name.startswith('Tile_'):
            continue
        values={cell._name:str(cell.Q.value) for cell in tile
                if isinstance(cell,HierarchyObject) and cell._def_name=='sg13cmos5l_dlhq_1'}
        tiles[tile._name]=dict(tile_type=tile._def_name,q=values)
    Path(path).write_text(json.dumps(dict(tiles=tiles),indent=2,sort_keys=True)+'\n')
    return tiles

@cocotb.test()
async def loaded_concurrent_uart_spi(d):
    div=int(os.environ['R1_DIV'])
    d.clk.value=0;d.rst_n.value=0;d.cfg_rst_n.value=0
    d.cfg_word.value=0;d.cfg_strobe.value=0;d.cfg_restart.value=0
    d.rx_i.value=1;d.miso_i.value=1;d.h_wlast.value=0
    d.h_wvalid.value=0;d.h_wdata.value=0;d.h_rready.value=0
    cocotb.start_soon(Clock(d.clk,20,unit='ns').start())
    await cycle(d,4);d.cfg_rst_n.value=1
    d.cfg_restart.value=1;await cycle(d);d.cfg_restart.value=0
    for word in BitFile.load(os.environ['R1_IMAGE']).words:
        d.cfg_word.value=word;d.cfg_strobe.value=1;await cycle(d)
        # Let the stretched frame strobe finish before another frame header.
        # The real management SPI path spaces words much farther apart.
        d.cfg_strobe.value=0;await cycle(d,5)
    await cycle(d,10);d.rst_n.value=1;await cycle(d,10)
    d._log.info('Compiler image loaded through frame FSM; starting pin-level traffic')
    if os.environ.get('R1_CFG_SNAPSHOT'):
        capture_configuration(d,os.environ['R1_CFG_SNAPSHOT'])

    activity={}
    async def uart_tx():
        for _ in range(20000):
            if int(d.tx_o.value)==0:break
            await cycle(d)
        else:raise AssertionError('configured UART never starts')
        start=get_sim_time(unit='ns')
        await cycle(d,div+div//2)
        value=0
        for bit in range(8):
            value|=int(d.tx_o.value)<<bit
            await cycle(d,div)
        assert value==0xa5 and int(d.tx_o.value)==1
        activity['uart_tx']=(start,get_sim_time(unit='ns'))

    async def uart_rx():
        await cycle(d,12)
        start=get_sim_time(unit='ns')
        for level in [0]+[(0x69>>i)&1 for i in range(8)]+[1]:
            d.rx_i.value=level;await cycle(d,div)
        activity['uart_rx']=(start,get_sim_time(unit='ns'))
        await cycle(d,div)

    async def spi_peer(expected=0x3c,record=True):
        for _ in range(20000):
            if not int(d.cs_n_o.value):break
            await cycle(d)
        else:raise AssertionError('configured SPI never selects')
        start=get_sim_time(unit='ns')
        value=0;previous=int(d.sck_o.value);count=0;elapsed=0;last_edge=None
        while not int(d.cs_n_o.value):
            now=int(d.sck_o.value)
            if not previous and now:
                if last_edge is not None:
                    assert elapsed-last_edge==2*int(os.environ['R1_HALF'])
                last_edge=elapsed
                value=(value<<1)|int(d.mosi_o.value);count+=1
            previous=now;await cycle(d);elapsed+=1
        assert count==8 and value==expected
        if record:activity['spi']=(start,get_sim_time(unit='ns'))

    tx=cocotb.start_soon(uart_tx());rx=cocotb.start_soon(uart_rx());spi=cocotb.start_soon(spi_peer())
    await put(d,0);await put(d,0xa5);await put(d,3);await put(d,0x3c)
    packets={}
    for _ in range(2):
        tag=await get(d);value=await get(d)
        assert tag not in packets;packets[tag]=value
    assert packets=={0:0x69,1:0xff}
    for task in (tx,rx,spi):await with_timeout(task,1000,'us')
    overlap=min(end for start,end in activity.values())-max(start for start,end in activity.values())
    assert len(activity)==3 and overlap>0, f'No simultaneous UART TX/RX and SPI activity: {activity}'
    d._log.info('Simultaneous UART TX/RX and SPI activity: %s ns; windows=%s',overlap,activity)
    if os.environ.get('R1_ACTIVITY'):
        Path(os.environ['R1_ACTIVITY']).write_text(json.dumps(dict(windows_ns=activity,overlap_ns=overlap),indent=2,sort_keys=True)+'\n')
    assert int(d.cs_n_o.value)==1
    if os.environ.get('R1_RESTART_PROBE')=='1':
        d._log.info('Resetting configured user logic for second SPI transfer')
        d.rst_n.value=0;await cycle(d,10);d.rst_n.value=1;await cycle(d,10)
        peer=cocotb.start_soon(spi_peer(0x5a,False))
        await put(d,3);await put(d,0x5a)
        assert [await get(d),await get(d)]==[1,0xff]
        await with_timeout(peer,1000,'us')
        d._log.info('Configured user reset and second SPI transfer passed')

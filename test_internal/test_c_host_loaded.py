"""Portable C loader/duplex API against actual SPI-loaded frozen G1 chip ports."""
import ctypes as ct
import os
from pathlib import Path
import cocotb
from cocotb.triggers import ClockCycles,Timer
try:
    from cocotb import bridge,resume
except ImportError:
    from cocotb._bridge import bridge,resume
from host.protocol import Op,State,tx_simple,tx_user_status,parse_byte
from test_bitstream import REAL_FABRIC,hold_x,settle_routing_loops,leave_fabric
from warp_host import reset,expect,parked

U8=ct.c_uint8
SIZE=ct.c_size_t
TRANSFER=ct.CFUNCTYPE(ct.c_int,ct.c_void_p,ct.POINTER(U8),ct.POINTER(U8),SIZE)
class Host(ct.Structure):
    _fields_=[("transfer",TRANSFER),("context",ct.c_void_p)]


@cocotb.test(skip=not REAL_FABRIC)
async def test_portable_c_host_loaded(dut):
    lib=ct.CDLL(str(Path(os.environ["WARP_C_HOST_LIB"]).resolve()))
    lib.warp_load_wbit.argtypes=[ct.POINTER(Host),ct.POINTER(U8),SIZE,SIZE]
    lib.warp_channel_duplex.argtypes=[ct.POINTER(Host),ct.POINTER(U8),SIZE,
        ct.c_int,ct.POINTER(U8),SIZE,SIZE,ct.POINTER(SIZE),ct.POINTER(SIZE)]
    raw=Path(os.environ["WARP_C_HOST_BITFILE"]).read_bytes()
    image=(U8*len(raw)).from_buffer_copy(raw)
    pins=await reset(dut)
    errors=[]
    commands=[]
    @resume
    async def spi(command):
        commands.append(command)
        return await pins.xfer(command)
    def transfer(context,tx,rx,n):
        try:
            result=spi(list(tx[:n]))
            assert len(result)==n
            for i,value in enumerate(result):rx[i]=value
            return 0
        except Exception as exc:
            errors.append(str(exc));return 1
    callback=TRANSFER(transfer)
    host=Host(callback,None)
    @bridge
    def load():
        return lib.warp_load_wbit(ct.byref(host),image,len(raw),16)
    # An old sticky error must not make a valid checked reload fail (BUG75).
    await pins.xfer([0xff])
    hold_x(dut,True);await Timer(1,unit="ns")
    rc=await load()
    assert rc==0,f"C checked load failed code={rc}: {errors}"
    await expect(pins,State.LOADED)
    assert parked(dut) and not errors
    hold_x(dut,False);await Timer(1,unit="ns")
    await settle_routing_loops(dut)
    await pins.xfer(tx_simple(Op.RUN));await expect(pins,State.RUNNING)
    data=[0,255,128,127]+list(range(27))
    outgoing=(U8*len(data))(*data);incoming=(U8*len(data))()
    nt,nr=SIZE(),SIZE()
    @bridge
    def exchange(rounds):
        return lib.warp_channel_duplex(ct.byref(host),outgoing,len(data),1,
            incoming,len(data),rounds,ct.byref(nt),ct.byref(nr))
    rc=await exchange(256)
    assert rc==0,f"C duplex code={rc}, progress={nt.value}/{nr.value}: {errors}"
    assert (nt.value,nr.value)==(len(data),len(data))
    assert list(incoming)==[(v+1)&255 for v in data]
    assert not errors
    status=await pins.status()
    assert status.user_attention and not status.ch_overflow
    assert parse_byte(await pins.xfer(tx_user_status()))==len(data)
    await pins.xfer(tx_simple(Op.USER_RESET));await ClockCycles(dut.clk,8)
    assert parse_byte(await pins.xfer(tx_user_status()))==0
    assert not (await pins.status()).user_attention
    await pins.xfer(tx_simple(Op.STOP));await expect(pins,State.LOADED)
    assert parked(dut)
    commands.clear()
    assert await exchange(1)==2
    assert nt.value==nr.value==0 and commands==[[1]]
    await leave_fabric(dut)

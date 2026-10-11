"""C transport against the existing independent transaction-level shell model.

This checks queue/order/state behavior, not cycle-level SPI or the intra-opcode
race (covered separately by the scripted wire-contract test).
"""
import ctypes as ct
import random
import shutil
import subprocess
import struct
import zlib
from pathlib import Path

import pytest

from refmodels.shell import (
    CH_READ, CH_WRITE, FIFO_DEPTH, LOADED, READ_ID, RUN, RUNNING,
    ShellModel, STOP,
)

U8 = ct.c_uint8
SIZE = ct.c_size_t
TRANSFER = ct.CFUNCTYPE(ct.c_int, ct.c_void_p, ct.POINTER(U8), ct.POINTER(U8), SIZE)


class Host(ct.Structure):
    _fields_ = [("transfer", TRANSFER), ("context", ct.c_void_p)]


@pytest.fixture(scope="module")
def driver(tmp_path_factory):
    cc = shutil.which("cc")
    if cc is None:
        pytest.fail("native host model checks require cc")
    source = Path(__file__).resolve().parents[1] / "c_host"
    output = tmp_path_factory.mktemp("c_host_model") / "host.so"
    subprocess.run([cc, "-std=c99", "-Wall", "-Wextra", "-Werror", "-pedantic",
                    "-shared", "-fPIC", str(source / "warp_host.c"), "-o", str(output)],
                   check=True, capture_output=True, text=True)
    lib = ct.CDLL(str(output))
    lib.warp_channel_write.argtypes = [ct.POINTER(Host), U8, ct.c_int, SIZE]
    lib.warp_channel_read.argtypes = [ct.POINTER(Host), ct.POINTER(U8), SIZE]
    for name in ("warp_channel_write_many", "warp_channel_read_many"):
        args = [ct.POINTER(Host), ct.POINTER(U8), SIZE]
        if "write" in name:
            args.append(ct.c_int)
        args.extend([SIZE, ct.POINTER(SIZE)])
        getattr(lib, name).argtypes = args
    lib.warp_poll.argtypes = [ct.POINTER(Host), ct.POINTER(U8)]
    lib.warp_read_status.argtypes = [ct.POINTER(Host), ct.POINTER(U8), ct.POINTER(U8)]
    lib.warp_read_id.argtypes = [ct.POINTER(Host), ct.POINTER(ct.c_uint16)]
    lib.warp_load_words.argtypes = [ct.POINTER(Host), ct.c_uint16,
                                    ct.POINTER(ct.c_uint32), SIZE, SIZE]
    lib.warp_load_wbit.argtypes = [ct.POINTER(Host), ct.POINTER(U8), SIZE, SIZE]
    return lib


class Bridge:
    def __init__(self, model, after=None):
        self.model = model
        self.after = after
        self.transactions = []
        self.errors = []
        self.callback = TRANSFER(self.transfer)
        self.host = Host(self.callback, None)

    def transfer(self, context, tx, rx, n):
        # Exceptions cannot propagate through a ctypes callback; retain them
        # and return IO failure so each test can explicitly inspect errors.
        try:
            command = list(tx[:n])
            self.transactions.append(command)
            result = self.model.transaction(command)
            for i, byte in enumerate(result):
                rx[i] = 0 if byte is None else byte
            if self.after:
                self.after(self.model, command)
            assert len(self.model.tx) <= FIFO_DEPTH
            assert len(self.model.rx) <= FIFO_DEPTH
            return 0
        except Exception as exc:
            self.errors.append(exc)
            return 1


def running_model(fabric=None):
    model = ShellModel(1, fabric)
    model.state = LOADED
    model.transaction([RUN])
    assert model.state == RUNNING
    return model


@pytest.mark.parametrize("seed", range(10))
def test_randomized_queue_service_preserves_bytes_and_last(driver, seed):
    rng = random.Random(seed)

    class Consumer:
        status = attention = 0
        received = []

        def user_reset(self):
            pass

        def settle(self, model):
            if model.tx and rng.randrange(4) == 0:
                self.received.append(model.tx.pop(0))

    fabric = Consumer()
    fabric.received = []
    model = running_model(fabric)
    bridge = Bridge(model)
    values = [rng.randrange(256) for _ in range(73)]
    data = (U8 * len(values))(*values)
    completed = SIZE()
    assert driver.warp_channel_write_many(ct.byref(bridge.host), data, len(values),
                                          1, 200, ct.byref(completed)) == 0
    # Drain remaining model queue without new writes.
    for _ in range(200):
        model.transaction([READ_ID])
    expected = [(v, int(i == len(values) - 1)) for i, v in enumerate(values)]
    assert fabric.received == expected
    assert completed.value == len(values)
    assert model.overflow == 0 and model.code == 0
    assert not bridge.errors


@pytest.mark.parametrize("seed", range(10))
def test_asynchronous_rx_arrivals_between_transactions(driver, seed):
    rng = random.Random(seed)
    values = [rng.randrange(256) for _ in range(61)]
    pending = iter(values)

    def arrive(model, command):
        if len(model.rx) < FIFO_DEPTH and rng.randrange(3) == 0:
            byte = next(pending, None)
            if byte is not None:
                model.rx.append(byte)

    model = running_model()
    bridge = Bridge(model, arrive)
    output = (U8 * len(values))()
    completed = SIZE()
    assert driver.warp_channel_read_many(ct.byref(bridge.host), output, len(values),
                                         200, ct.byref(completed)) == 0
    assert list(output) == values and completed.value == len(values)
    # Every consuming transaction is preceded by a non-destructive poll.
    for i, command in enumerate(bridge.transactions):
        if command[0] == CH_READ:
            assert i and bridge.transactions[i - 1] == [READ_ID]
    assert model.code == 0 and not bridge.errors


def test_full_empty_timeouts_and_stop_do_not_corrupt_queues(driver):
    model = running_model()
    bridge = Bridge(model)
    host = ct.byref(bridge.host)
    assert driver.warp_channel_write(host, 0, 0, 1) == 0
    assert driver.warp_channel_write(host, 255, 1, 1) == 0
    assert driver.warp_channel_write(host, 7, 0, 5) == 1
    assert model.tx == [(0, 0), (255, 1)] and not model.overflow
    byte = U8(123)
    assert driver.warp_channel_read(host, ct.byref(byte), 5) == 1
    assert byte.value == 123 and not model.rx
    model.transaction([STOP])
    assert driver.warp_channel_write(host, 7, 0, 5) == 2
    assert driver.warp_channel_read(host, ct.byref(byte), 5) == 2
    assert not model.tx and not model.rx and model.code == 0
    assert not bridge.errors


def test_sticky_flags_only_clear_on_explicit_read_status(driver):
    model = running_model()
    model.transaction([CH_WRITE, 0, 1])
    model.transaction([CH_WRITE, 0, 2])
    model.transaction([CH_WRITE, 0, 3])
    model.transaction([0xff])
    bridge = Bridge(model)
    status, error = U8(), U8()
    assert driver.warp_poll(ct.byref(bridge.host), ct.byref(status)) == 0
    assert status.value & 5 == 5 and model.code == 1 and model.overflow == 1
    assert driver.warp_read_status(ct.byref(bridge.host), ct.byref(status),
                                   ct.byref(error)) == 0
    assert status.value & 5 == 5 and error.value == 1
    assert model.code == 0 and model.overflow == 0
    assert model.tx == [(1, 0), (2, 0)] and not bridge.errors


def wbit(words, arch=1):
    body = b"".join(struct.pack(">I", word) for word in words)
    return b"WBIT" + struct.pack(">HHII", arch, 0, len(words), zlib.crc32(body)) + body


@pytest.mark.parametrize("chunk", [1, 3, 64])
@pytest.mark.parametrize("format", ["words", "wbit"])
def test_checked_loader_chunks_and_leaves_stopped(driver, chunk, format):
    words = [0xFAB0FAB1] + list(range(137))
    model = ShellModel(1)
    bridge = Bridge(model)
    if format == "words":
        data = (ct.c_uint32 * len(words))(*words)
        rc = driver.warp_load_words(ct.byref(bridge.host), 1, data, len(words), chunk)
    else:
        raw = wbit(words)
        data = (U8 * len(raw)).from_buffer_copy(raw)
        rc = driver.warp_load_wbit(ct.byref(bridge.host), data, len(raw), chunk)
    assert rc == 0 and model.state == LOADED
    assert model.forwarded == words and model.code == 0
    assert all(len(t) <= 1 + 4 * chunk for t in bridge.transactions if t[0] == 0x11)
    assert not any(t[0] == RUN for t in bridge.transactions)
    assert not bridge.errors


@pytest.mark.parametrize("mutation", ["magic", "crc", "length", "sync", "truncate"])
def test_corrupt_wbit_rejected_without_io(driver, mutation):
    raw = bytearray(wbit([0xFAB0FAB1, 7]))
    if mutation == "magic":
        raw[0] ^= 1
    elif mutation == "crc":
        raw[-1] ^= 1
    elif mutation == "length":
        raw[11] += 1
    elif mutation == "sync":
        raw = bytearray(wbit([0x12345678, 7]))
    else:
        raw = raw[:15]
    bridge = Bridge(ShellModel(1))
    data = (U8 * len(raw)).from_buffer_copy(raw)
    assert driver.warp_load_wbit(ct.byref(bridge.host), data, len(raw), 64) == 5
    assert not bridge.transactions and not bridge.errors


def test_loader_bad_arguments_and_state_arch_guards(driver):
    bridge = Bridge(ShellModel(1))
    host = ct.byref(bridge.host)
    data = (ct.c_uint32 * 1)(0xFAB0FAB1)
    for count, chunk in [(0, 1), (65536, 1), (1, 0), (1, 65)]:
        assert driver.warp_load_words(host, 1, data, count, chunk) == 4
    bad = (ct.c_uint32 * 1)(7)
    assert driver.warp_load_words(host, 1, bad, 1, 1) == 5
    assert not bridge.transactions
    assert driver.warp_load_words(host, 2, data, 1, 1) == 6
    assert bridge.transactions == [[1, 0, 0, 0, 0]]
    bridge.model.state = LOADED
    bridge.model.transaction([RUN])
    bridge.transactions.clear()
    assert driver.warp_load_words(host, 1, data, 1, 1) == 2
    assert all(t[0] == READ_ID for t in bridge.transactions)
    assert bridge.model.state == RUNNING and not bridge.errors


def test_loader_io_failure_is_not_retried(driver):
    model = ShellModel(1)
    commands = []

    @TRANSFER
    def callback(context, tx, rx, n):
        command = list(tx[:n])
        commands.append(command)
        response = model.transaction(command)
        for i, byte in enumerate(response):
            rx[i] = 0 if byte is None else byte
        return int(command[0] == 0x11)

    host = Host(callback, None)
    words = (ct.c_uint32 * 2)(0xFAB0FAB1, 7)
    assert driver.warp_load_words(ct.byref(host), 1, words, 2, 1) == 3
    assert commands[-1] == [0x11, 0xfa, 0xb0, 0xfa, 0xb1]
    assert sum(t[0] == 0x11 for t in commands) == 1
    assert model.forwarded == [0xFAB0FAB1]


def test_read_id_rejects_magic_and_preserves_output(driver):
    @TRANSFER
    def callback(context, tx, rx, n):
        for i in range(n):
            rx[i] = 0
        return 0

    host = Host(callback, None)
    arch = ct.c_uint16(0x1234)
    assert driver.warp_read_id(ct.byref(host), ct.byref(arch)) == 5
    assert arch.value == 0x1234


def test_loader_rejects_chip_reported_crc_error(driver):
    model = ShellModel(1)

    @TRANSFER
    def callback(context, tx, rx, n):
        command = list(tx[:n])
        if command[0] == 0x12:
            command[-1] ^= 1
        response = model.transaction(command)
        for i, byte in enumerate(response):
            rx[i] = 0 if byte is None else byte
        return 0

    host = Host(callback, None)
    words = (ct.c_uint32 * 1)(0xFAB0FAB1)
    assert driver.warp_load_words(ct.byref(host), 1, words, 1, 1) == 7
    assert model.state != LOADED


@pytest.mark.parametrize("prior_error", ["wrong_arch", "bad_command"])
def test_loader_recovers_after_sticky_error(driver, prior_error):
    model = ShellModel(1)
    if prior_error == "wrong_arch":
        model.transaction([0x10, 0, 2, 0, 1])
    else:
        model.transaction([0xff])
    assert model.code != 0
    bridge = Bridge(model)
    words = (ct.c_uint32 * 2)(0xFAB0FAB1, 7)
    assert driver.warp_load_words(ct.byref(bridge.host), 1, words, 2, 1) == 0
    assert model.state == LOADED and model.code == 0
    before_begin = bridge.transactions[:next(i for i, t in enumerate(bridge.transactions)
                                             if t[0] == 0x10)]
    assert [0x02, 0, 0] in before_begin
    assert not bridge.errors


def test_wbit_reserved_and_arch_bytes_match_python_format(driver):
    model = ShellModel(0x1234)
    bridge = Bridge(model)
    raw = bytearray(wbit([0xFAB0FAB1], arch=0x1234))
    raw[6:8] = b"\xa5\x5a"
    data = (U8 * len(raw)).from_buffer_copy(raw)
    assert driver.warp_load_wbit(ct.byref(bridge.host), data, len(raw), 1) == 0
    assert [0x10, 0x12, 0x34, 0, 1] in bridge.transactions
    assert model.state == LOADED and not bridge.errors

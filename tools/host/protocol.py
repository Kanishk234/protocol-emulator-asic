"""WARP host protocol (ARCHITECTURE.md v1, §2 host interface, §3 configuration loading).

Written from the specification only (not from the shell RTL). It is both the host software and
the reference the shell is tested against. Transport-independent: everything here builds or
parses byte sequences for one SPI transaction (CS low ... CS high). A transport (cocotb bench,
USB-SPI bridge) exchanges bytes full duplex and hands the MISO bytes back to `parse_*`.

Every transaction's first MISO byte (during the opcode) is STATUS.
"""

from dataclasses import dataclass
from enum import IntEnum
from typing import Iterable, List, Sequence
import zlib

ARCH_VERSION = 0x0003   # the chip being built (arch/CURRENT: warp_g1); 0x0002 was warp_g0, 0x0001 warp_tiny
ID_MAGIC = (0x57, 0x50)  # "WP"
SYNC_WORD = 0xFAB0FAB1


class Op(IntEnum):
    READ_ID = 0x01
    READ_STATUS = 0x02
    LOAD_BEGIN = 0x10
    LOAD_DATA = 0x11
    LOAD_END = 0x12
    RUN = 0x20
    STOP = 0x21
    USER_RESET = 0x22
    CH_WRITE = 0x30
    CH_READ = 0x31
    USER_STATUS = 0x32


class State(IntEnum):
    UNCONFIGURED = 0
    LOADING = 1
    LOADED = 2
    RUNNING = 3
    ERROR = 4


class ErrorCode(IntEnum):
    NONE = 0x00
    BAD_COMMAND = 0x01
    WRONG_ARCH = 0x10
    LENGTH = 0x11
    CRC = 0x12
    FORMAT = 0x13


@dataclass(frozen=True)
class Status:
    state: State
    rx_valid: bool
    tx_ready: bool
    ch_overflow: bool
    user_attention: bool
    error_pending: bool

    @classmethod
    def decode(cls, byte: int) -> "Status":
        s = (byte >> 5) & 0x7
        return cls(
            state=State(s) if s in State._value2member_map_ else s,  # unknown codes kept raw
            rx_valid=bool(byte & 0x10),
            tx_ready=bool(byte & 0x08),
            ch_overflow=bool(byte & 0x04),
            user_attention=bool(byte & 0x02),
            error_pending=bool(byte & 0x01),
        )

    def encode(self) -> int:
        return ((int(self.state) & 7) << 5 | self.rx_valid << 4 | self.tx_ready << 3
                | self.ch_overflow << 2 | self.user_attention << 1 | self.error_pending)

    @property
    def irq(self) -> bool:
        """HOST_IRQ as ARCHITECTURE §2.4 defines it."""
        return self.rx_valid or self.user_attention or self.state == State.ERROR


def be16(v: int) -> List[int]:
    return [(v >> 8) & 0xFF, v & 0xFF]


def be32(v: int) -> List[int]:
    return [(v >> 24) & 0xFF, (v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF]


def words_to_bytes(words: Iterable[int]) -> List[int]:
    out: List[int] = []
    for w in words:
        out += be32(w)
    return out


def crc32_words(words: Sequence[int]) -> int:
    """CRC-32 (IEEE 802.3, as zlib) over the words' big-endian bytes, in order (ARCHITECTURE §3)."""
    return zlib.crc32(bytes(words_to_bytes(words))) & 0xFFFFFFFF


# ---- transaction builders: the MOSI bytes of one CS-low transaction -------------------------

def tx_read_id() -> List[int]:
    return [Op.READ_ID, 0, 0, 0, 0]          # 4 dummy bytes clock out the ID


def tx_read_status() -> List[int]:
    return [Op.READ_STATUS, 0, 0]            # STATUS again, then ERROR_CODE


def tx_load_begin(n_words: int, arch_version: int = ARCH_VERSION) -> List[int]:
    if not 0 <= n_words <= 0xFFFF:
        raise ValueError("LENGTH is 16 bits")
    return [Op.LOAD_BEGIN] + be16(arch_version) + be16(n_words)


def tx_load_data(words: Sequence[int]) -> List[int]:
    return [Op.LOAD_DATA] + words_to_bytes(words)


def tx_load_end(crc: int) -> List[int]:
    return [Op.LOAD_END] + be32(crc)


def tx_simple(op: Op) -> List[int]:
    return [int(op)]


def tx_ch_write(data: int, last: bool = False) -> List[int]:
    return [Op.CH_WRITE, 1 if last else 0, data & 0xFF]


def tx_ch_read() -> List[int]:
    return [Op.CH_READ, 0]


def tx_user_status() -> List[int]:
    return [Op.USER_STATUS, 0]


class ArchMismatch(Exception):
    """The bitstream was built for a different architecture than the chip reports (READ_ID)."""


def checked_load_transactions(words: Sequence[int], file_arch: int, chip_arch: int,
                              chunk: int = 64) -> List[List[int]]:
    """The load for a bitstream file built for `file_arch`, on a chip whose READ_ID reported
    `chip_arch`. Refuses a mismatch before anything is sent (the shell would also reject it at
    LOAD_BEGIN with ERROR 0x10, but only after the host has started a load)."""
    if file_arch != chip_arch:
        raise ArchMismatch(f"bitstream is for architecture 0x{file_arch:04X}, "
                           f"the chip is 0x{chip_arch:04X}")
    return load_transactions(words, chunk, file_arch)


def load_transactions(words: Sequence[int], chunk: int = 64,
                      arch_version: int = ARCH_VERSION) -> List[List[int]]:
    """The whole load: LOAD_BEGIN, LOAD_DATA in chunks of `chunk` words, LOAD_END with the CRC."""
    txs = [tx_load_begin(len(words), arch_version)]
    for i in range(0, len(words), chunk):
        txs.append(tx_load_data(words[i:i + chunk]))
    txs.append(tx_load_end(crc32_words(words)))
    return txs


# ---- response parsers: the MISO bytes of the same transaction ------------------------------

def parse_status(miso: Sequence[int]) -> Status:
    return Status.decode(miso[0])


def parse_read_id(miso: Sequence[int]):
    """Returns (magic_ok, arch_version)."""
    return tuple(miso[1:3]) == ID_MAGIC, (miso[3] << 8) | miso[4]


def parse_read_status(miso: Sequence[int]):
    """Returns (Status, ErrorCode or raw int)."""
    code = miso[2]
    return Status.decode(miso[1]), ErrorCode(code) if code in ErrorCode._value2member_map_ else code


def parse_byte(miso: Sequence[int]) -> int:
    """CH_READ / USER_STATUS: the byte after the opcode."""
    return miso[1]

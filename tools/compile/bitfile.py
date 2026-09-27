"""WARP bitstream file (.wbit): what the compile flow writes and the host loads.

Layout (big-endian):
    magic      4 bytes  b"WBIT"
    arch       2 bytes  ARCH_VERSION the bitstream was built for (ARCHITECTURE.md §3)
    reserved   2 bytes  0
    n_words    4 bytes  number of configuration words
    crc32      4 bytes  CRC-32 of the words (as LOAD_END sends it)
    words      n_words x 4 bytes, starting with the sync word 0xFAB0FAB1

The words are exactly what LOAD_DATA sends. The host refuses a file whose `arch` differs from
the chip's READ_ID before sending anything; the shell refuses it again at LOAD_BEGIN.
"""

from dataclasses import dataclass
import struct
from typing import List

from host.protocol import SYNC_WORD, crc32_words

MAGIC = b"WBIT"
_HDR = struct.Struct(">4sHHII")


@dataclass
class BitFile:
    arch_version: int
    words: List[int]

    @property
    def crc(self) -> int:
        return crc32_words(self.words)

    def to_bytes(self) -> bytes:
        body = b"".join(struct.pack(">I", w) for w in self.words)
        return _HDR.pack(MAGIC, self.arch_version, 0, len(self.words), self.crc) + body

    @classmethod
    def from_bytes(cls, data: bytes) -> "BitFile":
        magic, arch, _, n, crc = _HDR.unpack_from(data)
        if magic != MAGIC:
            raise ValueError("not a WARP bitstream file")
        body = data[_HDR.size:]
        if len(body) != 4 * n:
            raise ValueError(f"truncated: {len(body)} bytes for {n} words")
        words = list(struct.unpack(f">{n}I", body))
        bf = cls(arch, words)
        if bf.crc != crc:
            raise ValueError("CRC mismatch in file")
        if not words or words[0] != SYNC_WORD:
            raise ValueError("first word is not the sync word")
        return bf

    @classmethod
    def load(cls, path) -> "BitFile":
        with open(path, "rb") as f:
            return cls.from_bytes(f.read())

    def save(self, path) -> None:
        with open(path, "wb") as f:
            f.write(self.to_bytes())


def words_from_fabulous_bin(data: bytes) -> List[int]:
    """FABulous's .bin is a 16-byte preamble, then the configuration words from the sync word on.
    Returns the words from the sync word (the preamble is metadata the ConfigFSM skips)."""
    sync = struct.pack(">I", SYNC_WORD)
    at = data.find(sync)
    if at < 0 or at % 4:
        raise ValueError("no word-aligned sync word in FABulous bitstream")
    body = data[at:]
    if len(body) % 4:
        raise ValueError("FABulous bitstream is not a whole number of words")
    return list(struct.unpack(f">{len(body) // 4}I", body))

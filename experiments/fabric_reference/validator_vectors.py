"""Independent zlib checksum oracle and public transaction mutations.

Does not parse the RTL. Input images use the pinned reference layout.
"""
import argparse
import hashlib
import json
import random
import struct
import zlib
from pathlib import Path

from frame_snapshot import decode

def generate(source: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    images = {name: (source / f"{name}.bin").read_bytes() for name in ("counter", "lfsr")}
    for data in images.values():
        decode(data)
    assert zlib.crc32(b"123456789") == 0xCBF43926
    cases = []
    a = images["counter"]

    def add(name, data=a, *, crc=None, arch=0x46524231, version=1,
            length=12024, mode=0, valid=0, error=1):
        assert len(data) % 4 == 0
        words = struct.unpack(f">{len(data)//4}I", data)
        (output / f"{name}.hex").write_text(
            "".join(f"{word:08x}\n" for word in words) or "00000000\n", encoding="ascii")
        cases.append(dict(name=name, words=len(words), crc=zlib.crc32(data) if crc is None else crc,
                          arch=arch, version=version, length=length, mode=mode,
                          valid=valid, error=error, sha256=hashlib.sha256(data).hexdigest()))

    for name, data in images.items():
        add(name, data, valid=1, error=0)
    for cut in (0, 4, 20, 80, 2000, 11960, 12020):
        add(f"truncated_{cut}", a[:cut], crc=zlib.crc32(a), error=0)
    add("padding_word", a + b"\0"*4, crc=zlib.crc32(a))
    add("memory_padding", a + b"\0"*(16384-len(a)), crc=zlib.crc32(a))
    for index in (0, 1, 2, 3, 4, 5, 20, 290, 3005):
        data = bytearray(a)
        data[index*4+3] ^= 1
        # Recompute CRC: structure must independently reject this image.
        add(f"structure_{index}", bytes(data))
    for index in (6, 19, 1499, 3004):
        data = bytearray(a)
        data[index*4] ^= 0x80
        add(f"payload_flip_{index}", bytes(data), crc=zlib.crc32(a))
    duplicate = a[:80] + a[20:80] + a[140:]
    add("duplicate_frame", duplicate)
    swapped = a[:20] + a[80:140] + a[20:80] + a[140:]
    add("swapped_frames", swapped)
    add("wrong_arch", arch=0x46524232)
    add("wrong_version", version=2)
    add("short_declared_length", length=12020)
    add("padded_declared_length", length=16384)
    add("wrong_crc", crc=zlib.crc32(a) ^ 1)
    add("last_word_commit", mode=1, valid=1, error=0)
    add("early_commit", mode=2, valid=1, error=0)
    add("abort_midstream", mode=3, error=0)
    add("reset_midstream", mode=4, error=0)
    add("metadata_changes_after_begin", mode=5, valid=1, error=0)
    add("commit_with_extra_word", a + b"\0"*4, crc=zlib.crc32(a), mode=6)
    rng = random.Random(0xA51C)
    for n in range(3):
        data = bytearray(a)
        for record in range(200):
            for row in range(14):
                struct.pack_into(">I", data, 24+record*60+row*4, rng.getrandbits(32))
        decode(data)
        add(f"random_payload_{n}", bytes(data), valid=1, error=0)
    # Valid transactions following sticky errors / abort / reset must recover.
    add("final_recovery", images["lfsr"], valid=1, error=0)
    (output / "cases.txt").write_text("".join(
        f"{c['name']} {c['words']} {c['crc']:08x} {c['arch']:08x} {c['version']} "
        f"{c['length']} {c['mode']} {c['valid']} {c['error']}\n" for c in cases), encoding="ascii")
    (output / "cases.json").write_text(json.dumps(cases, indent=2)+"\n", encoding="ascii")
    print(f"Generated {len(cases)} transaction cases using Python zlib CRC oracle")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    generate(args.source, args.output)

"""Prepare cached canonical images and controlled corruption for full-fabric tests."""
import argparse
import hashlib
import json
import zlib
from pathlib import Path
from frame_snapshot import decode

def generate(source: Path, output: Path) -> None:
    images = {n: (source / (n+".bin")).read_bytes() for n in ("counter", "lfsr")}
    for data in images.values():
        decode(data)
    damaged = bytearray(images["lfsr"])
    damaged[1404] ^= 1  # row payload, not frame-select address
    images["corrupt"] = bytes(damaged)
    data = images["lfsr"]
    images["duplicate"] = data[:80] + data[20:80] + data[140:]
    manifest = {}
    for name, data in images.items():
        (output / (name+".hex")).write_text(
            "".join(f"{b:02x}\n" for b in data.ljust(16384, b"\0")), encoding="ascii")
        manifest[name] = dict(bytes=len(data), crc=f"{zlib.crc32(data):08x}",
                              sha256=hashlib.sha256(data).hexdigest())
    (output / "images.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="ascii")
    # Exact fixed keys and hexadecimal values; sourced by the experiment runner.
    (output / "crc.env").write_text("".join(
        f"crc_{name}={metadata['crc']}\n" for name, metadata in manifest.items()), encoding="ascii")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    generate(args.source, args.output)

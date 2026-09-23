#!/usr/bin/env python3
"""Toolchain smoke test: sigrok-cli decodes a UART waveform from a VCD.

Writes a VCD of a known byte string sent as UART 8N1, runs sigrok's `uart`
decoder on it and checks the decoded bytes match. This checks the
VCD -> sigrok pipeline that the protocol tests (L3) will use; it does not
test the TRIPWIRE design.

Usage: python scripts/sigrok_smoke.py [workdir]
"""

import os
import re
import subprocess
import sys
import tempfile

BAUD = 115200
BIT_NS = round(1e9 / BAUD)
MESSAGE = b"TRIPWIRE"


def uart_edges(data):
    """Yield (time_ns, level) for an 8N1 idle-high line carrying `data`."""
    t = 0
    yield t, 1
    t += 10 * BIT_NS  # leading idle
    for byte in data:
        bits = [0] + [(byte >> i) & 1 for i in range(8)] + [1]  # start, LSB first, stop
        for b in bits:
            yield t, b
            t += BIT_NS
    yield t + 10 * BIT_NS, 1  # trailing idle


def write_vcd(path, data):
    with open(path, "w") as f:
        f.write("$timescale 1ns $end\n$scope module top $end\n")
        f.write("$var wire 1 ! tx $end\n$upscope $end\n$enddefinitions $end\n")
        last = None
        for t, level in uart_edges(data):
            if level != last:
                f.write(f"#{t}\n{level}!\n")
                last = level
            else:
                f.write(f"#{t}\n")


def main():
    workdir = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
    vcd = os.path.join(workdir, "uart_smoke.vcd")
    write_vcd(vcd, MESSAGE)
    out = subprocess.run(
        ["sigrok-cli", "-i", vcd, "-I", "vcd",
         "-P", f"uart:rx=tx:baudrate={BAUD}:format=hex",
         "-A", "uart=rx-data"],
        capture_output=True, text=True, check=True,
    ).stdout
    decoded = bytes(int(h, 16) for h in re.findall(r"uart-\d+: ([0-9A-Fa-f]{2})\b", out))
    if decoded != MESSAGE:
        print(f"FAIL: sigrok decoded {decoded!r}, expected {MESSAGE!r}\n{out}")
        return 1
    print(f"ok: sigrok uart decoded {decoded.decode()!r} from {vcd}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

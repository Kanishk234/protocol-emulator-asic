"""Read native mirroring completion; the Tcl call is not necessarily echoed."""
import re

def require_mirroring(text):
    values = re.findall(r"(?m)^\[INFO DPL-0020\] Mirrored (\d+) instances\s*$", text)
    if not values:
        raise ValueError("Missing native mirroring completion message")
    return int(values[-1])

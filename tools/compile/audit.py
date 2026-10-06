"""Check a compiled image and explicitly recorded input files against report hashes.

This is a local consistency check, not authentication, equivalence or timing
signoff. Reports without provenance cannot be audited by this tool.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from compile.bitfile import BitFile


def audit(report_path):
    report = json.loads(Path(report_path).read_text())
    provenance = report.get("provenance")
    if not provenance:
        raise ValueError("report has no provenance; rebuild with the current compiler")
    problems = []
    entries = [*provenance["inputs"], {"path": provenance["bitfile"],
                                     "sha256": provenance["bitfile_sha256"]}]
    for entry in entries:
        path = Path(entry["path"])
        if not path.is_file():
            problems.append(f"missing: {path}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            problems.append(f"changed: {path}")
    image = Path(provenance["bitfile"])
    if image.is_file():
        try:
            bf = BitFile.load(image)
            if (f"0x{bf.arch_version:04X}" != report["arch_version"] or
                    len(bf.words) != report["words"] or f"0x{bf.crc:08X}" != report["crc32"]):
                problems.append("bitstream header/payload disagrees with report")
        except (ValueError, struct.error, OSError) as exc:
            # Parsing errors must reject the audit, including truncated headers.
            problems.append(f"invalid bitstream: {exc}")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report", type=Path)
    args = ap.parse_args()
    try:
        problems = audit(args.report)
    except (ValueError, KeyError, OSError) as exc:
        ap.exit(1, f"audit: {exc}\n")
    if problems:
        ap.exit(1, "audit: FAIL\n" + "\n".join(problems) + "\n")
    print("audit: PASS (listed inputs and image match; not chip signoff)")


if __name__ == "__main__":
    main()

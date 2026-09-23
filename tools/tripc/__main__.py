"""Command line: python -m tripc PROGRAM.trw [-p NAME=VALUE ...] [-o image.json] [-r report.md]"""

import argparse
import json
import sys

from .compiler import TrwError, compile_file
from .expr import evaluate


def main():
    ap = argparse.ArgumentParser(prog="tripc", description="Compile a TRIPWIRE .trw program.")
    ap.add_argument("program")
    ap.add_argument("-p", "--param", action="append", default=[], help="override a param: NAME=EXPR")
    ap.add_argument("-o", "--output", help="write the image as JSON")
    ap.add_argument("-r", "--report", help="write the report (Markdown); default: print it")
    args = ap.parse_args()
    params = {}
    for p in args.param:
        name, _, expr = p.partition("=")
        params[name] = evaluate(expr, {})
    try:
        image, report = compile_file(args.program, params)
    except TrwError as e:
        print(f"tripc: {e}", file=sys.stderr)
        return 1
    if args.output:
        with open(args.output, "w") as f:
            json.dump(image, f, indent=1)
    if args.report:
        with open(args.report, "w") as f:
            f.write(report)
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())

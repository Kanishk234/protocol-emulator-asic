"""Command line: python -m tripc PROGRAM.trw [-p NAME=VALUE ...] [-o image.json] [-r report.md]"""

import argparse
import json
import pathlib
import sys

from .compiler import TrwError, compile_file
from .expr import evaluate
from .response import analyze_queries, response_report


def main():
    ap = argparse.ArgumentParser(prog="tripc", description="Compile a TRIPWIRE .trw program.")
    ap.add_argument("program")
    ap.add_argument("-p", "--param", action="append", default=[], help="override a param: NAME=EXPR")
    ap.add_argument("-o", "--output", help="write the image as JSON")
    ap.add_argument("-r", "--report", help="write the report (Markdown); default: print it")
    ap.add_argument('--response-queries', help='JSON mapping of conditional single-token response contracts')
    ap.add_argument('--response-results', help='write full conditional response results as JSON')
    args = ap.parse_args()
    if args.response_results and not args.response_queries:
        ap.error('--response-results requires --response-queries')
    params = {}
    for p in args.param:
        name, _, expr = p.partition("=")
        params[name] = evaluate(expr, {})
    try:
        image, report = compile_file(args.program, params)
    except TrwError as e:
        print(f"tripc: {e}", file=sys.stderr)
        return 1
    results = None
    if args.response_queries:
        try:
            queries = json.loads(pathlib.Path(args.response_queries).read_text())
            results = analyze_queries(image, queries)
        except (OSError, ValueError) as e:
            print(f'tripc: response query: {e}', file=sys.stderr)
            return 2
        report += '\n' + response_report(results)
        if args.response_results:
            pathlib.Path(args.response_results).write_text(json.dumps(results, indent=2) + '\n')
    if args.output:
        with open(args.output, "w") as f:
            json.dump(image, f, indent=1)
    if args.report:
        with open(args.report, "w") as f:
            f.write(report)
    else:
        print(report)
    return 2 if results and any(r['status'] != 'bounded' for r in results.values()) else 0


if __name__ == "__main__":
    sys.exit(main())

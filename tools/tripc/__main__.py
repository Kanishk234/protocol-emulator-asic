"""Command line: python -m tripc PROGRAM.trw [-p NAME=VALUE ...] [-o image.json] [-r report.md]"""

import argparse
import json
import pathlib
import sys

from .compiler import TrwError, compile_file
from .expr import evaluate
from .response import analyze_queries, response_report
from .linked_budget import compose_linked_response, linked_budget_report
from .periodic_channel import analyze_compiled_channel


def main():
    ap = argparse.ArgumentParser(prog="tripc", description="Compile a TRIPWIRE .trw program.")
    ap.add_argument("program")
    ap.add_argument("-p", "--param", action="append", default=[], help="override a param: NAME=EXPR")
    ap.add_argument("-o", "--output", help="write the image as JSON")
    ap.add_argument("-r", "--report", help="write the report (Markdown); default: print it")
    ap.add_argument('--response-queries', help='JSON mapping of conditional single-token response contracts')
    ap.add_argument('--response-results', help='write full conditional response results as JSON')
    ap.add_argument('--linked-budget', help='JSON edge-gap/setup assumptions for conditional linked-response composition')
    ap.add_argument('--channel-schedule', help='JSON arrival and service schedule for one blocking channel')
    args = ap.parse_args()
    if args.response_results and not args.response_queries:
        ap.error('--response-results requires --response-queries')
    if args.linked_budget and not args.response_queries:
        ap.error('--linked-budget requires --response-queries')
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
    channel = None
    if args.channel_schedule:
        try:
            schedule = json.loads(pathlib.Path(args.channel_schedule).read_text())
            channel = analyze_compiled_channel(image, schedule)
        except (OSError, ValueError) as e:
            print(f'tripc: channel schedule: {e}', file=sys.stderr)
            return 2
        report += (
            '\n## Declared channel schedule\n\n'
            'Conditional on an initially empty channel, static bindings and the supplied '
            'periodic arrival and service opportunities. The compiler does not establish '
            'that the running program supplies those opportunities.\n\n'
            f'```json\n{json.dumps({"schedule": schedule, "result": channel}, indent=2)}\n```\n'
        )
    if args.response_queries:
        try:
            queries = json.loads(pathlib.Path(args.response_queries).read_text())
            results = analyze_queries(image, queries)
            if args.linked_budget:
                budget = json.loads(pathlib.Path(args.linked_budget).read_text())
                for result in results.values():
                    result['linked_budget'] = compose_linked_response(image, result, budget)
        except (OSError, ValueError) as e:
            print(f'tripc: response query: {e}', file=sys.stderr)
            return 2
        report += '\n' + response_report(results)
        if args.linked_budget:
            report += '\n' + linked_budget_report(results)
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
    if channel and channel['status'] != 'no_overrun':
        return 2
    return 2 if results and any(r['status'] != 'bounded' or
                              r.get('linked_budget', {}).get('status', 'conditional_pass') != 'conditional_pass'
                              for r in results.values()) else 0


if __name__ == "__main__":
    sys.exit(main())

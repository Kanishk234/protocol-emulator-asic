"""Audit retained OpenSTA max-fanout reports without running EDA.

Blank printed slack is allowed; every violated row and the explicit report
count must agree. This audits report evidence, not complete load connectivity,
physical acceptance or configured timing. JSON includes the source SHA256.
"""
import argparse
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import unittest

NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
ROW = re.compile(rf"^(\S+)\s+({NUMBER})\s+({NUMBER})(?:\s+({NUMBER}))?\s+\(VIOLATED\)$")


def parse_report(text):
    headings = list(re.finditer(r"^max fanout\s*$", text, re.M))
    totals = re.findall(r"^max fanout violation count (\d+)\s*$", text, re.M)
    if len(headings) != 1 or len(totals) != 1:
        raise ValueError("Require one max fanout table and one explicit violation count")
    after = text[headings[0].end():]
    header = re.match(r"\s*Pin[ \t]+Limit[ \t]+Fanout[ \t]+Slack[ \t]*\n-+[ \t]*\n", after)
    if not header:
        raise ValueError("Missing fanout table column header")
    rows = []
    seen = set()
    for line in after[header.end():].splitlines():
        if not line.strip():
            break
        match = ROW.fullmatch(line.strip())
        if not match:
            raise ValueError(f"Malformed fanout row: {line}")
        pin, limit_s, load_s, slack_s = match.groups()
        limit, load = Decimal(limit_s), Decimal(load_s)
        if pin in seen or limit <= 0 or load <= limit:
            raise ValueError(f"Duplicate or inconsistent violation: {line}")
        seen.add(pin)
        slack = Decimal(slack_s) if slack_s is not None else None
        if slack is not None and slack != limit - load:
            raise ValueError(f"Slack disagrees with limit minus fanout: {line}")
        group = ("FrameData" if re.fullmatch(r"FrameData\[\d+\]", pin)
                 else "FrameStrobe" if re.fullmatch(r"FrameStrobe\[\d+\]", pin)
                 else "other")
        rows.append({"pin": pin, "limit": str(limit), "fanout": str(load),
                     "slack": str(slack) if slack is not None else None,
                     "group": group})
    count = int(totals[0])
    if len(rows) != count:
        raise ValueError(f"Table has {len(rows)} rows but report says {count}")
    return {"violation_count": count, "groups": dict(Counter(r["group"] for r in rows)),
            "load_histograms": {group: dict(sorted(Counter(r["fanout"] for r in rows
                if r["group"] == group).items())) for group in sorted({r["group"] for r in rows})},
            "rows": rows, "acceptance_claim": False}


class ParserChecks(unittest.TestCase):
    SAMPLE = "max fanout\n\nPin Limit Fanout Slack\n----------------\nFrameData[0] 8 17 -9 (VIOLATED)\nW2MID[1] 8 9 (VIOLATED)\n\nmax fanout violation count 2\n"

    def test_blank_slack_is_retained(self):
        result = parse_report(self.SAMPLE)
        self.assertEqual(result["groups"], {"FrameData": 1, "other": 1})
        self.assertIsNone(result["rows"][1]["slack"])

    def test_zero_count(self):
        text = self.SAMPLE.replace("FrameData[0] 8 17 -9 (VIOLATED)\nW2MID[1] 8 9 (VIOLATED)\n", "").replace("count 2", "count 0")
        self.assertEqual(parse_report(text)["violation_count"], 0)

    def test_invalid_evidence_fails(self):
        for text in [self.SAMPLE.replace("count 2", "count 3"),
                     self.SAMPLE.replace("-9 (VIOLATED)", "-8 (VIOLATED)"),
                     self.SAMPLE.replace("W2MID[1]", "FrameData[0]"),
                     self.SAMPLE.replace("8 9 (VIOLATED)", "8 garbage (VIOLATED)"),
                     self.SAMPLE.replace("8 9 (VIOLATED)", "8 8 (VIOLATED)"),
                     self.SAMPLE + self.SAMPLE]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_report(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="*", type=Path)
    parser.add_argument("--expect-count", type=int)
    parser.add_argument("--expect-limit", type=Decimal)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(ParserChecks)
        if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():
            return 1
    if not args.reports and not args.self_test:
        parser.error("Provide retained reports or --self-test")
    results = []
    for path in args.reports:
        data = path.read_bytes()
        result = parse_report(data.decode("utf-8"))
        if args.expect_count is not None and result["violation_count"] != args.expect_count:
            raise ValueError(f"Unexpected count in {path}")
        if args.expect_limit is not None and any(Decimal(r["limit"]) != args.expect_limit for r in result["rows"]):
            raise ValueError(f"Unexpected limit in {path}")
        result.update({"path": str(path), "sha256": hashlib.sha256(data).hexdigest()})
        results.append(result)
    if results:
        print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Reject missing or unsuccessful JUnit/cocotb XML evidence."""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


def check_xml(path, minimum_cases=1):
    """Return executed passing case names, allowing multi-suite documents."""
    if (not isinstance(minimum_cases, int) or isinstance(minimum_cases, bool)
            or minimum_cases < 1):
        raise ValueError("minimum cases must be a positive integer")
    root = ET.parse(path).getroot()
    if root.tag not in ("testsuite", "testsuites"):
        raise ValueError("expected a testsuite or testsuites document")
    if any(next(root.iter(tag), None) is not None
           for tag in ("failure", "error", "skipped")):
        raise ValueError("XML contains failures, errors or skipped tests")
    for suite in root.iter():
        if suite.tag in ("testsuite", "testsuites"):
            for field in ("failures", "errors", "skipped"):
                try:
                    count = int(suite.get(field, "0"))
                except ValueError as exc:
                    raise ValueError("invalid XML suite counter: " + field) from exc
                if count != 0:
                    raise ValueError("nonzero XML suite counter: " + field)
    cases = list(root.iter("testcase"))
    if len(cases) < minimum_cases:
        raise ValueError(f"expected at least {minimum_cases} executed passing cases; found {len(cases)}")
    return [case.get("name") for case in cases]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--minimum-cases", type=int, default=1)
    args = parser.parse_args()
    try:
        names = check_xml(args.path, args.minimum_cases)
    except (OSError, ValueError, ET.ParseError) as exc:
        parser.error(str(exc))
    print(f"Verified {len(names)} executed passing test cases: {args.path}")


if __name__ == "__main__":
    main()

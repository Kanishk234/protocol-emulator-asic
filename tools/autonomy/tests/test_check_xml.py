from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

from autonomy.check_xml import check_xml


@pytest.mark.parametrize("body", [
    "", "<testsuite>", "<testsuite/>", "<testsuites/>",
    '<report><testcase name="fake"/></report>',
    '<testsuite><testcase><failure/></testcase></testsuite>',
    '<testsuite><testcase><error/></testcase></testsuite>',
    '<testsuite><testcase><skipped/></testcase></testsuite>',
    *[f'<testsuites {field}="{value}"><testsuite><testcase/></testsuite></testsuites>'
      for field in ("failures", "errors", "skipped")
      for value in ("1", "-1", "oops")],
])
def test_reject_false_green_xml(tmp_path, body):
    path = tmp_path / "results.xml"
    path.write_text(body)
    with pytest.raises((ValueError, ET.ParseError)):
        check_xml(path)


def test_reject_missing_xml(tmp_path):
    with pytest.raises(OSError):
        check_xml(tmp_path / "missing.xml")


def test_accept_multiple_suites_and_require_minimum(tmp_path):
    path = tmp_path / "results.xml"
    path.write_text('<testsuites failures="0"><testsuite errors="0">'
                    '<testcase name="first"/></testsuite><testsuite skipped="0">'
                    '<testcase name="second"/></testsuite></testsuites>')
    assert check_xml(path) == ["first", "second"]
    assert check_xml(path, 2) == ["first", "second"]
    with pytest.raises(ValueError, match="at least 3"):
        check_xml(path, 3)


@pytest.mark.parametrize("minimum", [0, -1, True, 1.5])
def test_invalid_minimum(tmp_path, minimum):
    with pytest.raises(ValueError, match="positive integer"):
        check_xml(tmp_path / "unused", minimum)


def test_cli_exit_codes_from_protocol_working_directory(tmp_path):
    checker = Path(__file__).resolve().parents[1] / "check_xml.py"
    path = tmp_path / "results.xml"
    command = [sys.executable, str(checker), str(path)]
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode != 0
    path.write_text('<testsuite><testcase name="passed"/></testsuite>')
    assert subprocess.run(command, cwd=tmp_path, capture_output=True).returncode == 0
    assert subprocess.run(command + ["--minimum-cases", "2"], cwd=tmp_path,
                          capture_output=True).returncode != 0

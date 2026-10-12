"""Reject incomplete/invalid native delay queries; preserve absent-path evidence."""
from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "test_internal"))
from cloud_hold_allocation import parse_queries

HEADER = "CELL\tMODE\tSTATE\tSLACK_NS\tSTART\tEND\n"
DATA = HEADER + "hold1\tmin\tCONSTRAINED\t0.12\tff/Q\tff/D\n" + "hold1\tmax\tNO_CONSTRAINED_PATH\tNA\tNA\tNA\n"


def test_missing_path_is_retained_not_zero():
    result = parse_queries(DATA, {"hold1"})
    assert result["min"]["hold1"]["slack_ns"] == "0.12"
    assert result["max"]["hold1"] == {"state": "NO_CONSTRAINED_PATH", "slack_ns": "NA", "start": "NA", "end": "NA"}


@pytest.mark.parametrize("text", [
    DATA.split("\n", 1)[1],
    DATA + DATA.splitlines()[1] + "\n",
    HEADER + DATA.splitlines()[1] + "\n",
    DATA.replace("hold1", "hold2"),
    DATA.replace("\tmin\t", "\tbad\t"),
    DATA.replace("\t0.12\t", "\tNaN\t"),
    DATA.replace("\t0.12\t", "\tInfinity\t"),
    DATA.replace("\tff/Q\t", "\tNA\t"),
    DATA.replace("\tNA\tNA\tNA", "\t0\tNA\tNA"),
    DATA.replace("NO_CONSTRAINED_PATH", "UNKNOWN"),
])
def test_incomplete_or_invalid_observation_rejected(text):
    with pytest.raises(ValueError): parse_queries(text, {"hold1"})

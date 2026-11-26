from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from spi_tick_pipeline_trial import ROOT, SOURCE_SHA, TIMER_OLD, restore, sha, variant


def test_registered_tick_edit_is_reversible_and_rejects_wrong_source():
    source = ROOT/'protocols/spi_ctrl/spi_ctrl_top.v'
    assert sha(source) == SOURCE_SHA
    original = source.read_text()
    candidate = variant(original)
    assert restore(candidate) == original
    assert source.read_text() == original
    for wrong in (candidate, original.replace(TIMER_OLD, ''), original+TIMER_OLD):
        with pytest.raises(ValueError):
            variant(wrong)
    with pytest.raises(ValueError):
        restore(original)


def test_ungated_timer_registered_tick_remains_isolated_and_mode_specific():
    source=ROOT/'protocols/spi_ctrl/spi_ctrl_top.v';original=source.read_text()
    candidate=variant(original,ungated_timer=True)
    assert ".en(1'b1), .tc(tick_early)" in candidate
    assert restore(candidate,ungated_timer=True)==original
    assert source.read_text()==original and sha(source)==SOURCE_SHA
    with pytest.raises(ValueError):restore(candidate)
    with pytest.raises(ValueError):restore(variant(original),ungated_timer=True)
    with pytest.raises(ValueError):variant(original,ungated_timer='true')

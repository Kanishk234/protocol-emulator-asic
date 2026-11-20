from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from placement_trial import admit_frequency_log


def test_native_default_frequency_cannot_qualify_requested_50mhz():
    with pytest.raises(ValueError):
        admit_frequency_log("Max frequency for clock 'run': 40.60 MHz (PASS at 12.00 MHz)",50)


def test_explicit_request_does_not_require_model_timing_to_pass():
    admit_frequency_log("Max frequency for clock 'run': 40.60 MHz (FAIL at 50.00 MHz)",50)

from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from spi_timer_trial import admit_status,variant


def test_experiment_rejects_missing_or_duplicate_timer_hook():
    for source in ('en(other)', '.en(timing), .tc(tick) .en(timing), .tc(tick)'):
        with pytest.raises(ValueError):variant(source)


def test_exact_single_enable_change_preserves_the_remaining_source():
    source='module unchanged; /* prefix */ .en(timing), .tc(tick); endmodule'
    changed=variant(source)
    assert changed=="module unchanged; /* prefix */ .en(1'b1), .tc(tick); endmodule"


def test_pinned_sby_pass_metadata_requires_completed_pdr_proof():
    proof='summary: engine_0 (abc pdr) returned PASS\nDONE (PASS, rc=0)\n'
    admit_status('PASS 0 1\n',proof)
    for status in ('FAIL 0 1','UNKNOWN','PASS FAIL',''):
        with pytest.raises(ValueError):admit_status(status,proof)
    with pytest.raises(ValueError):admit_status('PASS 0 1','incomplete')

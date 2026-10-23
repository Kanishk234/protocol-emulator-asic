from pathlib import Path
import subprocess

import pytest
import yaml

import wire600_mux_precheck as trial


def test_drc_classification_keeps_outside_and_boundary_crossing_markers():
    text = 'top\n---\nRule\n---\n 12.0um 40.0um 13.0um 41.0um\n 11.9um 40.0um 12.1um 41.0um\n'
    result = trial.classify(text, ['12', '40', '248.8', '231.34'])
    assert result['total'] == 2
    assert len(result['outside_macro']) == 1
    assert not result['violation_waiver']


@pytest.mark.parametrize('text', ['top\n', 'top\nRule\n 1um 2um 3um\n',
                                      'top\nRule\n 2um 2um 1um 3um\n'])
def test_malformed_drc_fails_closed(text):
    with pytest.raises(ValueError):
        trial.classify(text, [0, 0, 10, 10])


def test_wrong_provenance_rejected_before_packaging(tmp_path):
    with pytest.raises(ValueError, match='provenance'):
        trial.package(tmp_path, {}, tmp_path/'package')
    assert not (tmp_path/'package').exists()


def test_workflow_uses_unchanged_precheck_and_exact_artifact():
    root = Path(__file__).resolve().parents[2]
    w = yaml.safe_load((root/'.github/workflows/gds-wire600-mux-precheck.yaml').read_text())
    assert w['jobs']['precheck']['steps'] == [{'uses': 'TinyTapeout/tt-gds-action/precheck@ihp-cmos5l'}]
    steps = w['jobs']['package']['steps']
    download = next(s['with'] for s in steps if 'download-artifact@' in s.get('uses', ''))
    assert download['run-id'] == 39883160399
    info = yaml.safe_load((trial.FIXTURES/'mux_submission_info.yaml').read_text())
    assert info['project']['tiles'] == '6x4'
    assert info['project']['clock_hz'] == 50000000
    assert info['project']['top_module'] == 'tt_um_tripwire'
    for step in steps:
        if 'run' in step:
            subprocess.run(['bash', '-n'], input=step['run'], text=True, check=True)

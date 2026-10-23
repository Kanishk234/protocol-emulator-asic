import json
from pathlib import Path
import subprocess

import pytest
import yaml

import wire600_mux_signoff as trial


def make_tail(root):
    for i, (pattern, key) in enumerate(trial.FRESH_METRICS.items()):
        p = root / pattern.replace('*', str(i))
        p.parent.mkdir(parents=True)
        p.write_text(json.dumps({'metrics': {key: 0}}))
    for stage, view in [('magic-streamout', 'mag_gds'), ('klayout-streamout', 'klayout_gds')]:
        p = root / ('20-'+stage)
        p.mkdir()
        gds = p/'test.gds'
        gds.write_bytes(b'test fixture')
        (p/'state_out.json').write_text(json.dumps({view: str(gds.resolve())}))


def test_fresh_tail_never_claims_official_signoff(tmp_path):
    make_tail(tmp_path)
    result = trial.collect(tmp_path)
    assert result['diagnostic_tail_pass']
    assert not result['official_signoff']
    assert not result['klayout_drc_verified']


@pytest.mark.parametrize('value', [None, 1, -1, False, '0'])
def test_missing_or_failing_drc_is_rejected(tmp_path, value):
    make_tail(tmp_path)
    p = next(tmp_path.glob('*-magic-drc/state_out.json'))
    p.write_text(json.dumps({'metrics': {'magic__drc_error__count': value}}))
    with pytest.raises(ValueError, match='Fresh signoff metric'):
        trial.collect(tmp_path)


def test_inherited_other_streamout_gds_is_rejected(tmp_path):
    make_tail(tmp_path)
    magic = next(tmp_path.glob('*-magic-streamout/test.gds'))
    klayout = next(tmp_path.glob('*-klayout-streamout/state_out.json'))
    klayout.write_text(json.dumps({'klayout_gds': str(magic.resolve())}))
    with pytest.raises(ValueError, match='fresh klayout'):
        trial.collect(tmp_path)


def test_missing_source_fails_closed(tmp_path):
    with pytest.raises(FileNotFoundError):
        trial.validate_source(tmp_path, {})


def test_workflow_and_stock_tail_preserve_scope():
    root = Path(__file__).resolve().parents[2]
    w = yaml.safe_load((root/'.github/workflows/gds-wire600-mux-signoff.yaml').read_text())
    steps = w['jobs']['signoff']['steps']
    download = next(s['with'] for s in steps if 'download-artifact@' in s.get('uses', ''))
    assert download['run-id'] == 39868597887
    assert 'Magic.DRC' in trial.STEPS and 'Netgen.LVS' in trial.STEPS
    assert not any('Routing' in s or 'Resizer' in s for s in trial.STEPS)
    assert trial.PROFILE['omitted_unused_views'] == ['json_h', 'vh']
    for s in steps:
        if 'run' in s:
            subprocess.run(['bash', '-n'], input=s['run'], text=True, check=True)

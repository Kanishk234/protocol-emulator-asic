import hashlib
import json
from pathlib import Path
import subprocess

import pytest
import yaml

from cache_gate_profile import BASE, EXCLUDED, prepare

ROOT = Path(__file__).resolve().parents[2]


def fixture(root):
    source = root/'src'
    source.mkdir()
    (source/'trw_chip.v').write_text('// exact fixture\n')
    config = dict(CLOCK_PERIOD=20, EXTRA_EXCLUDED_CELLS=BASE, GRT_RESIZER_HOLD_SLACK_MARGIN=.125)
    (source/'config.json').write_text(json.dumps(config))
    evidence = root/'evidence'
    evidence.mkdir()
    (evidence/'candidate.json').write_text(json.dumps(dict(
        reference_config_sha256=hashlib.sha256((source/'config.json').read_bytes()).hexdigest(),
        candidate_rtl_inventory={'trw_chip.v': hashlib.sha256((source/'trw_chip.v').read_bytes()).hexdigest()})))
    selected = root/'spikes/phase2_stock_flow/selected_profile.json'
    selected.parent.mkdir(parents=True)
    selected.write_text(json.dumps(dict(profile='portable_cpad_drive2_tx_pending_level_cache_no_owner',changes={})))
    return evidence


def test_exact_one_setting_and_unchanged_rtl(tmp_path):
    evidence = fixture(tmp_path)
    before = json.loads((tmp_path/'src/config.json').read_text())
    receipt = prepare(tmp_path, evidence)
    after = json.loads((tmp_path/'src/config.json').read_text())
    assert after == {**before, 'EXTRA_EXCLUDED_CELLS': EXCLUDED}
    assert not receipt['physical_qualified'] and not receipt['official_signoff']
    with pytest.raises(ValueError): prepare(tmp_path, evidence)


@pytest.mark.parametrize('name', ['src/trw_chip.v', 'src/config.json'])
def test_source_drift_fails_before_mutation(tmp_path, name):
    evidence = fixture(tmp_path)
    p=tmp_path/name
    p.write_text(p.read_text()+' drift')
    before=(tmp_path/'src/config.json').read_bytes()
    with pytest.raises(ValueError): prepare(tmp_path, evidence)
    assert (tmp_path/'src/config.json').read_bytes()==before


def test_workflow_preserves_every_native_control_and_gate():
    folder=ROOT/'.github/workflows'
    before=yaml.safe_load((folder/'gds-official-dev4-cache-no-owner-screen.yaml').read_text())
    after=yaml.safe_load((folder/'gds-official-dev4-cache-gate-screen.yaml').read_text())
    assert after['on']=={'workflow_dispatch':{}}
    assert before['jobs']['screen']['env']==after['jobs']['screen']['env']
    steps=after['jobs']['screen']['steps']
    extra=[s for s in steps if s['name']=='Prepare bound A22OI mapping exclusion']
    assert len(extra)==1
    rest=[s for s in steps if s not in extra]
    assert len(rest)==len(before['jobs']['screen']['steps'])
    for a,b in zip(before['jobs']['screen']['steps'],rest):
        if a.get('uses','').startswith('actions/upload-artifact'):
            assert a['uses']==b['uses'] and b['if']=='always()'
            assert b['with']['path'].startswith(a['with']['path'])
        else: assert a==b, a['name']
    for s in steps:
        if 'run' in s: subprocess.run(['bash','-n'],input=s['run'],text=True,check=True)


def test_reviewed_gate_config_hash_is_admitted_to_tile_preflight():
    from official_nov9_preflight import CONFIGS
    evidence=json.loads((ROOT/'spikes/phase2_stock_flow/cache_gate/candidate.json').read_text())
    assert evidence['candidate_config_sha256'] in CONFIGS
    assert evidence['changed_fields']==['EXTRA_EXCLUDED_CELLS']

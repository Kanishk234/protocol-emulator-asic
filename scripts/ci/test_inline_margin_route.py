import copy
from pathlib import Path
import pytest
from combined_physical_route import validate_provenance
from inline_margin_route import PROFILE


@pytest.mark.parametrize('key,value',[('qualified',False),('estimated_margin_pass',False),
    ('inline_electrical_margin_audited',False),('post_antenna_buffers',23),
    ('qualification_replayed_from',1),('physical_changes_repeated',True)])
def test_exact_complete_qualified_receipt_required(key,value):
    receipt=copy.deepcopy(PROFILE['gate_receipt']);receipt[key]=value
    with pytest.raises(ValueError):validate_provenance(PROFILE['run_binding'],receipt,PROFILE)


def test_calibrated_source_and_all_margins_are_bound():
    validate_provenance(PROFILE['run_binding'],PROFILE['gate_receipt'],PROFILE)
    assert PROFILE['source_run']==38777752196
    gate=PROFILE['gate_receipt']
    assert gate['added_buffers']==123 and gate['post_antenna_buffers']==24
    assert gate['estimated_margin_limit']==.45
    assert all(v<=.45 for d in gate['estimated_margin_maximum'].values() for v in d.values())
    assert max(gate['loads'].values())<=6


def test_workflow_routes_saved_qualified_state_without_new_grt():
    import yaml
    root=Path(__file__).resolve().parents[2]
    w=yaml.safe_load((root/'.github/workflows/gds-inline-margin-route.yaml').read_text())
    steps=w['jobs']['harden']['steps']
    download=next(s['with'] for s in steps if 'download-artifact@' in s.get('uses',''))
    assert download['run-id']==38777752196
    assert download['name']=='gds-inline-margin-qualify-38777752196'
    assert any(s.get('run')=='python workflow-src/scripts/ci/inline_margin_route.py' for s in steps)
    assert not any('GlobalRouting' in s.get('run','') or 'docker build' in s.get('run','') for s in steps)
    first=next(s for s in steps if 'upload-artifact@' in s.get('uses',''))
    assert first['if']=="always() && hashFiles('runs/inline-margin-route/extracted_gates.json') != ''"

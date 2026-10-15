import copy
from pathlib import Path
import pytest
from combined_physical_route import validate_provenance
from fanout_slew_route import PROFILE
from fanout_slew_plan import BINDING


@pytest.mark.parametrize('group,key,value',[('run','id',1),('run','head_sha','wrong'),('run','conclusion','failure'),('gates','qualified',False),('gates','minimum_fast_hold_ns',.01),('gates','resized_cells',1),('gates','added_buffers',7),('gates','post_antenna_batches',0)])
def test_exact_success_and_complete_repair_receipt_required(group,key,value):
    run=copy.deepcopy(PROFILE['run_binding']);gates=copy.deepcopy(PROFILE['gate_receipt'])
    (run if group=='run' else gates)[key]=value
    with pytest.raises(ValueError):validate_provenance(run,gates,PROFILE)


def test_source_baseline_and_plan_match_exact_extracted_lineage():
    assert PROFILE['source_run']==38676308492
    assert PROFILE['gate_receipt']['source_run']==BINDING['source_run']==38668749394
    assert PROFILE['baseline_nl']=='runs/fanout-finish-route/drt/1-openroad-detailedrouting/tt_um_tripwire.nl.v'
    assert PROFILE['gate_receipt']['post_antenna_buffers']==3
    assert PROFILE['output_root']=='runs/fanout-slew-route'
    assert PROFILE['saved_extraction_root']=='runs/fanout-slew-source-extracted-timing'
    validate_provenance(PROFILE['run_binding'],PROFILE['gate_receipt'],PROFILE)


def test_workflow_uses_successful_screen_and_shared_stock_continuation():
    import yaml
    root=Path(__file__).resolve().parents[2];w=yaml.safe_load((root/'.github/workflows/gds-fanout-slew-route.yaml').read_text())
    steps=w['jobs']['harden']['steps'];d=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==38676308492 and d['with']['name']=='gds-fanout-slew-screen-38676308492'
    assert any(s.get('run')=='python workflow-src/scripts/ci/fanout_slew_route.py' for s in steps)
    assert not any('GlobalRouting' in s.get('run','') or 'docker build' in s.get('run','') for s in steps)


def test_gate_evidence_is_published_before_bulk_only_with_fresh_receipt():
    import yaml
    root=Path(__file__).resolve().parents[2]
    w=yaml.safe_load((root/'.github/workflows/gds-fanout-slew-route.yaml').read_text())
    uploads=[s for s in w['jobs']['harden']['steps'] if 'upload-artifact@' in s.get('uses','')]
    assert len(uploads)==2
    summary,bulk=uploads
    assert summary['if']=="always() && hashFiles('runs/fanout-slew-route/extracted_gates.json') != ''"
    assert 'electrical_summary.json' in summary['with']['path']
    assert 'corner_summary.json' in summary['with']['path']
    assert 'extracted_gates.json' in summary['with']['path']
    assert summary['with']['name']!=bulk['with']['name']
    assert 'runs/**' in bulk['with']['path']

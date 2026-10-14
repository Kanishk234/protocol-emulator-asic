import copy
from pathlib import Path
import pytest
from combined_physical_route import validate_provenance
from sram_residual_route import PROFILE
from sram_residual_plan import BINDING


@pytest.mark.parametrize('group,key,value',[('run','id',1),('run','head_sha','wrong'),('run','conclusion','failure'),('gates','qualified',False),('gates','minimum_fast_hold_ns',.01),('gates','resized_cells',1),('gates','added_buffers',7),('gates','post_antenna_batches',0)])
def test_exact_success_and_complete_repair_receipt_required(group,key,value):
    run=copy.deepcopy(PROFILE['run_binding']);gates=copy.deepcopy(PROFILE['gate_receipt'])
    (run if group=='run' else gates)[key]=value
    with pytest.raises(ValueError):validate_provenance(run,gates,PROFILE)


def test_source_baseline_and_plan_match_exact_extracted_lineage():
    assert PROFILE['source_run']==38637997316
    assert PROFILE['gate_receipt']['source_run']==BINDING['source_run']==38621290574
    assert PROFILE['baseline_nl']=='runs/final-combined-route/drt/1-openroad-detailedrouting/tt_um_tripwire.nl.v'
    assert PROFILE['gate_receipt']['post_antenna_buffers']==3
    assert PROFILE['output_root']=='runs/sram-residual-route'
    assert PROFILE['saved_extraction_root']=='runs/sram-residual-source-extracted-timing'
    validate_provenance(PROFILE['run_binding'],PROFILE['gate_receipt'],PROFILE)


def test_workflow_uses_successful_screen_and_shared_stock_continuation():
    import yaml
    root=Path(__file__).resolve().parents[2];w=yaml.safe_load((root/'.github/workflows/gds-sram-residual-route.yaml').read_text())
    steps=w['jobs']['harden']['steps'];d=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==38637997316 and d['with']['name']=='gds-sram-residual-screen-38637997316'
    assert any(s.get('run')=='python workflow-src/scripts/ci/sram_residual_route.py' for s in steps)
    assert not any('GlobalRouting' in s.get('run','') or 'docker build' in s.get('run','') for s in steps)

from pathlib import Path
import pytest
import yaml
from route_restore_screen import validate_provenance,SOURCE_RUN,SOURCE_SHA


def source():
    run=dict(id=SOURCE_RUN,head_sha=SOURCE_SHA,head_branch='main',conclusion='success',path='.github/workflows/gds-route-segment-export.yaml')
    gates=dict(source_run=38283838612,added_buffers=7,resized_cells=1,minimum_fast_hold_ns=.05,
        physical_screen_only=True,custom_image=True,official_signoff=False,
        route_segment_capture_only=True,checkpoint_restoration_tested=False,
        qualified=False,timing_antenna_qualified=True,electrical_qualified=False)
    return run,gates


def test_export_success_is_not_qualification():validate_provenance(*source())


@pytest.mark.parametrize('fault',['wrong_head','failed_export','missing_receipt','claimed_signoff'])
def test_wrong_source_or_receipt_refused(fault):
    run,gates=source()
    if fault=='wrong_head':run['head_sha']='other'
    elif fault=='failed_export':run['conclusion']='failure'
    elif fault=='missing_receipt':gates.pop('electrical_qualified')
    else:gates['official_signoff']=True
    with pytest.raises(ValueError):validate_provenance(run,gates)


def test_workflow_reads_exact_export_and_uses_no_edit_runner():
    root=Path(__file__).resolve().parents[2]
    w=yaml.safe_load((root/'.github/workflows/gds-route-restore-screen.yaml').read_text());steps=w['jobs']['harden']['steps']
    d=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==SOURCE_RUN
    assert any(s.get('run')=='python workflow-src/scripts/ci/route_restore_screen.py' for s in steps)

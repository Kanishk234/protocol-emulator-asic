from pathlib import Path
import pytest
import yaml
from electrical_incremental_screen import validate_provenance,SOURCE_RUN,SOURCE_SHA


def source():
    r=dict(id=SOURCE_RUN,head_sha=SOURCE_SHA,head_branch='main',conclusion='success',path='.github/workflows/gds-route-restore-screen.yaml')
    g=dict(exact_segment_roundtrip=True,unchanged_routes_preserved=True,
        unchanged_netlist=True,physical_change_applied=False,official_signoff=False,
        source_run=38293466146,matched_timing=True,no_edit_incremental=True,
        diagnostic_only=True,source_physical_qualified=False)
    return r,g


def test_exact_diagnostic_source_does_not_claim_physical_qualification():validate_provenance(*source())


@pytest.mark.parametrize('fault',['source','geometry','signoff'])
def test_unverified_source_refused(fault):
    r,g=source()
    if fault=='source':r['head_sha']='other'
    elif fault=='geometry':g['unchanged_routes_preserved']=False
    else:g['official_signoff']=True
    with pytest.raises(ValueError):validate_provenance(r,g)


def test_workflow_binds_source_and_separate_output():
    root=Path(__file__).resolve().parents[2];w=yaml.safe_load((root/'.github/workflows/gds-electrical-incremental-screen.yaml').read_text())
    steps=w['jobs']['harden']['steps'];d=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==SOURCE_RUN
    assert any(s.get('run')=='python workflow-src/scripts/ci/electrical_incremental_screen.py' for s in steps)

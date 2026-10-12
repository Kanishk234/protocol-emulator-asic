import copy
from pathlib import Path
import pytest
import yaml
from electrical_repair_screen import validate_provenance, SOURCE_RUN, SOURCE_SHA


def source():
    run=dict(id=SOURCE_RUN,head_sha=SOURCE_SHA,head_branch='main',conclusion='success',path='.github/workflows/gds-sram-bank-electrical-screen.yaml')
    gates=dict(source_run=38172640071,clean_from_rtl=True,stock_classic=True,
        custom_image=False,added_cells_by_policy=0,relocated_instances=16,qualified=True,
        minimum_fast_hold_ns=.05,physical_screen_only=True,official_signoff=False,
        native_postgrt_electrical_repair=True,setup_repair_target_ns=0.0,
        hold_repair_target_ns=.125,slew_margin_pct=10,cap_margin_pct=10)
    return run,gates


def test_exact_legacy_timing_source_accepted(): validate_provenance(*source())


@pytest.mark.parametrize('key,value',[('id',0),('head_sha','wrong'),('head_branch','other'),('conclusion','failure'),('path','other')])
def test_wrong_source_refused(key,value):
    run,gates=source();run[key]=value
    with pytest.raises(ValueError): validate_provenance(run,gates)


def test_wrong_gate_refused():
    run,gates=source();gates['minimum_fast_hold_ns']=0
    with pytest.raises(ValueError): validate_provenance(run,gates)


def test_workflow_frozen_hardware_exact_source_and_separate_output():
    root=Path(__file__).resolve().parents[2]
    w=yaml.safe_load((root/'.github/workflows/gds-electrical-repair-screen.yaml').read_text())
    job=w['jobs']['harden'];steps=job['steps']
    download=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert download['with']['run-id']==SOURCE_RUN
    assert job['env']['CANDIDATE_SHA']=='3393eea9a58c5cad9077cc360a8515d0e5ec8284'
    assert any(s.get('run')=='python workflow-src/scripts/ci/electrical_repair_screen.py' for s in steps)
    upload=next(s for s in steps if 'upload-artifact@' in s.get('uses',''))
    assert 'runs/electrical-repair-screen/**' in upload['with']['path']

from pathlib import Path
import pytest
from combined_physical_route import validate_provenance,SOURCE_RUN,SOURCE_SHA


def source():
    run=dict(id=SOURCE_RUN,head_sha=SOURCE_SHA,head_branch='main',conclusion='success',path='.github/workflows/gds-combined-physical-screen.yaml')
    gates=dict(source_run=38305592967,qualified=True,added_buffers=76,resized_cells=8,minimum_fast_hold_ns=.05,all_original_connections_audited=True,source_detailed_wires_cleared=True,full_reroute=True,custom_image=True,physical_screen_only=True,official_signoff=False)
    return run,gates


@pytest.mark.parametrize('group,key,value',[(0,'id',1),(0,'head_sha','wrong'),(0,'conclusion','failure'),(1,'qualified',False),(1,'minimum_fast_hold_ns',.01),(1,'added_buffers',75),(1,'resized_cells',9),(1,'all_original_connections_audited',False)])
def test_exact_successful_gate_required(group,key,value):
    args=list(source());args[group][key]=value
    with pytest.raises(ValueError):validate_provenance(*args)


def test_workflow_exact_source_and_no_repair_replay():
    import yaml
    root=Path(__file__).resolve().parents[2];w=yaml.safe_load((root/'.github/workflows/gds-combined-physical-route.yaml').read_text())
    steps=w['jobs']['harden']['steps'];d=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==SOURCE_RUN and d['with']['name']==f'gds-combined-physical-screen-{SOURCE_RUN}'
    validate_provenance(*source())
    code=(root/'scripts/ci/combined_physical_route.py').read_text()
    assert 'source_run=SOURCE_RUN' in code and 'continue_route(config,source,output' in code
    assert 'OpenROAD.GlobalRouting' not in code and 'docker' not in code

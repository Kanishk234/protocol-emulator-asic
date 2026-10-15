import json
from pathlib import Path
import pytest
import inline_margin_gl as target
from postgrt_timing import CORNERS


@pytest.mark.parametrize('fault',[None,'hash','hold','setup','antenna','electrical','corner'])
def test_full_extracted_evidence_required_before_protocol_gl(tmp_path,monkeypatch,fault):
    monkeypatch.setattr(target,'validate_electrical',lambda *a,**k:{'route_run':38784492656})
    root=tmp_path/'runs/extracted-timing';stage=root/'11-openroad-stapostpnr';stage.mkdir(parents=True)
    metrics={f'timing__{kind}__ws__corner:{c}':(.1 if kind=='hold' else 0) for c in CORNERS for kind in ('setup','hold')}
    if fault=='hold':metrics[f'timing__hold__ws__corner:{CORNERS[0]}']=.01
    if fault=='setup':metrics[f'timing__setup__ws__corner:{CORNERS[1]}']=-.01
    (root/'corner_summary.json').write_text(json.dumps(metrics))
    ant=root/'02-openroad-checkantennas';ant.mkdir()
    (ant/'or_metrics_out.json').write_text(json.dumps({'antenna__violating__nets':int(fault=='antenna'),'antenna__violating__pins':0}))
    for c in CORNERS:
        d=stage/c;d.mkdir()
        text=c+'\nmax slew violation count 0\nmax fanout violation count 0\nmax cap violation count 0\n'
        if fault=='electrical' and c==CORNERS[1]:text=c+'\nmax fanout\ndriver/X 8 9 (VIOLATED)\nmax slew violation count 0\nmax fanout violation count 1\nmax cap violation count 0\n'
        (d/'checks.rpt').write_text(text)
    if fault=='corner':(stage/CORNERS[1]/'checks.rpt').unlink()
    if fault:
        with pytest.raises((ValueError,FileNotFoundError)):target.validate(tmp_path,{},'wrong' if fault=='hash' else target.NETLIST_SHA)
    else:assert target.validate(tmp_path,{},target.NETLIST_SHA)['route_run']==38784492656


def test_workflow_uses_exact_route_and_icarus13_without_changing_tests():
    import yaml
    root=Path(__file__).resolve().parents[2]
    w=yaml.safe_load((root/'.github/workflows/l3-inline-margin-routed-gl.yaml').read_text())
    steps=w['jobs']['l3']['steps'];d=next(s['with'] for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['run-id']==38784492656
    assert d['name']=='gds-inline-margin-route-38784492656'
    assert target.PROFILE['run_binding']['head_sha']=='88850b1241a4d83609537602dc7d8c7857a9c3a8'
    commands='\n'.join(s.get('run','') for s in steps)
    assert 'iverilog_13.0-1_amd64.deb' in commands
    assert 'COCOTB_TEST_MODULES=test_l3' in commands
    assert 'from inline_margin_gl import validate' in commands

import json
from pathlib import Path
import pytest
import native_post_antenna_route as runner
from native_wire150_route import PROFILE
from native_wire150_screen import configure
from test_native_post_antenna_route import receipts


@pytest.mark.parametrize('fault',[None,'run','sha','path','hold','qualified'])
def test_wire150_profile_binds_exact_passing_source(fault):
    run,gates,recipe=receipts()
    run.update(id=PROFILE['source_run'],head_sha=PROFILE['source_sha'],path=PROFILE['source_workflow'])
    recipe['hold_target_ns']=.125
    if fault=='run':run['id']=runner.SOURCE_RUN
    if fault=='sha':run['head_sha']=runner.SOURCE_SHA
    if fault=='path':run['path']='.github/workflows/gds-native-post-timing-antenna-screen.yaml'
    if fault=='hold':recipe['hold_target_ns']=.10
    if fault=='qualified':gates['qualified']=False
    if fault:
        with pytest.raises(ValueError):runner.validate_provenance(run,gates,recipe,PROFILE)
    else:runner.validate_provenance(run,gates,recipe,PROFILE)


def test_prepare_generates_wire150_recipe_before_download(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path('src').mkdir()
    Path('src/config_merged.json').write_text(json.dumps(dict(CLOCK_PERIOD=20,PL_TARGET_DENSITY_PCT=56)))
    monkeypatch.setattr(runner,'fingerprints',lambda root:{'src/example.v':'trusted'})
    writes={}
    monkeypatch.setattr(Path,'write_text',lambda path,text:writes.update({str(path):text}))
    runner.prepare(config_transform=configure)
    cfg=json.loads(writes['/tmp/native-trusted-config.json'])
    assert cfg['GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH']==150
    assert cfg['GRT_RESIZER_HOLD_SLACK_MARGIN']==.125
    assert cfg['GRT_ALLOW_CONGESTION'] is False and cfg['CLOCK_PERIOD']==20
    assert json.loads(writes['/tmp/native-trusted-files.json'])=={'src/example.v':'trusted'}


def test_route_workflow_uses_only_reviewed_screen():
    import yaml
    path=Path(__file__).resolve().parents[2]/'.github/workflows/gds-native-wire150-hold125-route.yaml'
    job=yaml.safe_load(path.read_text())['jobs']['harden'];steps=job['steps']
    download=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    prepare=next(s for s in steps if s['name'].startswith('Prepare trusted'))
    assert steps.index(prepare)<steps.index(download)
    assert download['with']['run-id']==PROFILE['source_run']
    assert download['with']['name']==f"gds-native-wire150-hold125-area1-{PROFILE['source_run']}"
    assert 'native_wire150_route.py --prepare' in prepare['run']
    assert job['timeout-minutes']==350

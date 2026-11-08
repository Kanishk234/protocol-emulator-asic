import hashlib
import json
from copy import deepcopy
from pathlib import Path
import pytest
from host_idle_drt_repair import configure, validate_source


@pytest.fixture
def source(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / 'artifact'
    base = root / 'runs/host-idle-drt-diagnostic'
    step = base / '1-openroad-detailedrouting'
    step.mkdir(parents=True)
    state = {'metrics': {'route__drc_errors': 96}, 'sdf': {'old': 'stale.sdf'}}
    for key, suffix in [('odb','odb'),('def','def'),('nl','nl.v'),('pnl','pnl.v'),('sdc','sdc')]:
        name = 'tt_um_tripwire.' + suffix
        (step / name).write_text('frozen ' + key)
        state[key] = str(tmp_path / step.relative_to(root) / name)
    (step / 'state_out.json').write_text(json.dumps(state))
    (step / 'config.json').write_text(json.dumps(dict(CLOCK_PERIOD=20,DRT_OPT_ITERS=42,DRT_ANTENNA_REPAIR_ITERS=0)))
    result = dict(source_run=42394957445,iteration_limit=42,reported_drc_errors=96,
                  physical_qualified=False,extracted_timing_performed=False,
                  post_route_antenna_qualified=False,official_gds_qualified=False)
    (base / 'diagnostic_result.json').write_text(json.dumps(result))
    run = dict(id=42433571153,head_sha='bound-sha',head_branch='main',conclusion='success')
    artifact = dict(id=13605087039,digest='sha256:frozen',expired=False)
    manifest = dict(run=deepcopy(run),artifact=deepcopy(artifact),
        files={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
               for p in root.rglob('*') if p.is_file()})
    return root, manifest, run, artifact


def test_bounded_repair_retains_all_other_settings():
    old = dict(CLOCK_PERIOD=20,MACROS={'m': {'location':[12,40]}},DRT_OPT_ITERS=42)
    new = configure(old)
    assert new['DRT_OPT_ITERS']==12 and new['DRT_ANTENNA_REPAIR_ITERS']==0
    allowed={'OPENROAD_THREADS','DRT_OPT_ITERS','DRT_SAVE_DRC_REPORT_ITERS','DRT_SAVE_SNAPSHOTS','DRT_ANTENNA_REPAIR_ITERS'}
    assert {k:v for k,v in new.items() if k not in allowed}=={k:v for k,v in old.items() if k not in allowed}
    assert old['DRT_OPT_ITERS']==42 and new['MACROS'] is not old['MACROS']


@pytest.mark.parametrize('period',[None,18,25])
def test_changed_clock_rejects(period):
    with pytest.raises(ValueError):configure({'CLOCK_PERIOD':period})


def test_bound_checkpoint_clears_inherited_timing_views(source):
    root,m,r,a=source
    state=validate_source(*source)
    assert all(state[k] is None for k in ('spef','sdf','lib'))
    original=json.loads((root/'runs/host-idle-drt-diagnostic/1-openroad-detailedrouting/state_out.json').read_text())
    assert original['sdf']=={'old':'stale.sdf'}


@pytest.mark.parametrize('part,key,value',[(2,'head_sha','other'),(2,'conclusion','failure'),(3,'digest','sha256:other'),(3,'expired',True)])
def test_wrong_source_provenance_rejects(source,part,key,value):
    source[part][key]=value
    with pytest.raises(ValueError,match='provenance'):validate_source(*source)


def test_changed_view_bytes_reject(source):
    root,*_=source
    (root/'runs/host-idle-drt-diagnostic/1-openroad-detailedrouting/tt_um_tripwire.odb').write_bytes(b'other')
    with pytest.raises(ValueError,match='Changed DRT'):validate_source(*source)


@pytest.mark.parametrize('kind',['foreign_view','false_signoff','wrong_drc','wrong_clock'])
def test_invalid_checkpoint_semantics_reject_after_hash_check(source,kind):
    root,m,r,a=source
    relative='runs/host-idle-drt-diagnostic/'
    if kind=='false_signoff':relative+='diagnostic_result.json';key='official_gds_qualified';value=True
    elif kind=='wrong_clock':relative+='1-openroad-detailedrouting/config.json';key='CLOCK_PERIOD';value=25
    else:
        relative+='1-openroad-detailedrouting/state_out.json'
        key='odb' if kind=='foreign_view' else 'metrics'
        value='/foreign/tt_um_tripwire.odb' if kind=='foreign_view' else {'route__drc_errors':0}
    path=root/relative;data=json.loads(path.read_text());data[key]=value;path.write_text(json.dumps(data))
    m['files'][relative]=hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError):validate_source(*source)

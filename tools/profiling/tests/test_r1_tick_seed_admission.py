"""Reject mismatched producers/seeds before staging a native image."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'spikes/r1'))
from sa_functional import prepare


@pytest.mark.parametrize('mutation',[
    'seed','seed_type','control_seed','clock','producer','image','control_image','native_claim',
])
def test_bounded_seed_admission_rejects_wrong_identity(tmp_path,mutation):
    catalog=json.loads((ROOT/'spikes/r1/spi_tick_seed_compile_sources.json').read_text())
    row=dict(run=str(catalog['run']['id']),source_sha=catalog['run']['head_sha'],
             actual_native_loading=False,model_timing_characterized=False)
    control=dict(row,placement_seed=1,
                 image_sha256='c6b96ef02d052b405f58b9742acbff02c0fd0c4e31f6d278e09649d1a5e6991f')
    expected=catalog['seeds']['2']
    candidate=dict(row,placement_seed=2,image_sha256=expected['image_sha256'],
                   clock_constraint=deepcopy(expected['clock_constraint']))
    if mutation=='seed':candidate['placement_seed']=3
    elif mutation=='seed_type':candidate['placement_seed']='2'
    elif mutation=='control_seed':control['placement_seed']=True
    elif mutation=='clock':candidate['clock_constraint']['bel']='X0Y4/A'
    elif mutation=='producer':candidate['run']='different'
    elif mutation=='image':candidate['image_sha256']='0'*64
    elif mutation=='control_image':control['image_sha256']='0'*64
    elif mutation=='native_claim':candidate['actual_native_loading']=True
    trial=tmp_path/'trial'
    for name,data in [('control',control),('candidate',candidate)]:
        folder=trial/name;folder.mkdir(parents=True)
        (folder/'result.json').write_text(json.dumps(data))
    with pytest.raises(ValueError):
        prepare(tmp_path/'capsule',tmp_path/'native',trial,tmp_path/'out',trial_kind='spi_tick_seed2')
    assert not (tmp_path/'out').exists()


@pytest.mark.parametrize('case,wrong',[('candidate',False),('candidate',1),('control',True)])
def test_ungated_source_marker_cannot_reuse_other_variant(tmp_path,case,wrong):
    catalog=json.loads((ROOT/'spikes/r1/spi_tick_ungated_compile_sources.json').read_text())
    expected=catalog['seeds']['1'];common=dict(run=str(catalog['run']['id']),
        source_sha=catalog['run']['head_sha'],actual_native_loading=False,
        model_timing_characterized=False,placement_seed=1)
    cases={'control':dict(common,ungated_timer=False,
              image_sha256='c6b96ef02d052b405f58b9742acbff02c0fd0c4e31f6d278e09649d1a5e6991f'),
           'candidate':dict(common,ungated_timer=True,image_sha256=expected['image_sha256'],
              clock_constraint=expected['clock_constraint'])}
    cases[case]['ungated_timer']=wrong
    for name,data in cases.items():
        folder=tmp_path/'trial'/name;folder.mkdir(parents=True)
        (folder/'result.json').write_text(json.dumps(data))
    with pytest.raises(ValueError,match='Ungated timer source identity differs'):
        prepare(tmp_path/'capsule',tmp_path/'native',tmp_path/'trial',tmp_path/'out',
                trial_kind='spi_tick_ungated')
    assert not (tmp_path/'out').exists()

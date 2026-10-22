import ast
import copy
import hashlib
import json
from pathlib import Path
import subprocess

import pytest
import yaml

import wire600_clean_route as base
import wire600_clean_gl as base_gl
import wire600_extracted_route as route
import wire600_extracted_gl as gl
from wire600_extracted_reserve import REVIEW,validate_change


def test_new_profile_is_explicit_and_old_defaults_stay_bound():
    p=route.profile()
    assert p['binding']['run_binding']['id']==39824026639
    assert p['screen_root']==Path('runs/wire600-extracted-clean')
    assert p['output']==Path('runs/wire600-extracted-route')
    assert p['proposal_review']==REVIEW
    assert p['connectivity_audit'] is validate_change
    assert base.review()['run_binding']['id']==39718836864
    assert base.ROOT==Path('runs/wire600-clean-reproduction')
    assert p['binding']['files'][p['binding']['netlist']] != base.review()['files'][base.review()['netlist']]


def test_explicit_bundle_cannot_fall_back_to_old_receipts(tmp_path):
    selected=route.profile();bound=copy.deepcopy(selected['binding'])
    bound['files']={}
    old=tmp_path/base.ROOT/'reproduction.json';old.parent.mkdir(parents=True);old.write_text('{}')
    with pytest.raises(FileNotFoundError):
        base.validate_bundle(tmp_path,bound['run_binding'],bound=bound,screen_root=selected['screen_root'])
    with pytest.raises(ValueError,match='provenance'):
        base.validate_bundle(tmp_path,base.review()['run_binding'],bound=bound,screen_root=selected['screen_root'])


def test_wrappers_forward_same_selected_profile(monkeypatch):
    selected=route.profile();calls=[]
    monkeypatch.setattr(route.base,'main',lambda p:calls.append(p))
    route.main();assert calls==[selected]
    monkeypatch.setattr(gl,'replay_validate',lambda *a,**kw:calls.append((a,kw)))
    gl.validate(Path('/artifact'),{'id':39824026639})
    assert calls[-1]==((Path('/artifact'),{'id':39824026639}),dict(bound=selected['binding'],screen_root=selected['screen_root']))


@pytest.mark.parametrize('filename',['gds-wire600-extracted-route.yaml','l3-wire600-extracted-gl.yaml'])
def test_workflows_pin_selected_clean_artifact_and_parse(filename):
    root=Path(__file__).resolve().parents[2]
    workflow=yaml.safe_load((root/'.github/workflows'/filename).read_text())
    job=next(iter(workflow['jobs'].values()))
    download=next(s['with'] for s in job['steps'] if 'download-artifact@' in s.get('uses',''))
    assert download['name']=='wire600-extracted-clean-evidence-area1-39824026639'
    assert download['run-id']==39824026639
    text='\n'.join(s.get('run','') for s in job['steps'])
    if filename.startswith('l3'):
        assert 'COCOTB_TEST_MODULES=test_l3' in text
        assert 'from wire600_extracted_gl import validate' in text
    else:
        assert 'wire600_extracted_route.py' in text
        assert job['timeout-minutes']==350
    for step in job['steps']:
        if 'run' not in step:continue
        script=step['run'];subprocess.run(['bash','-n'],input=script,text=True,check=True)
        for marker,end in [("<<'PY'\n",'PY'),("<<'PYCODE'\n",'PYCODE')]:
            if marker in script:ast.parse(script.split(marker,1)[1].split('\n'+end,1)[0])


def test_explicit_replay_uses_new_root_and_never_old_global_defaults(tmp_path):
    newroot=Path('runs/new-clean')
    receipt=dict(clean_synthesis=True,source_artifact_downloaded=False,
                 exact_source_reproduced=True,repaired_measured_gates_pass=True,
                 official_signoff=False,qualified=False,final_state='state.json')
    p=tmp_path/newroot/'reproduction.json';p.parent.mkdir(parents=True);p.write_text(json.dumps(receipt))
    (tmp_path/'state.json').write_text('{}')
    (tmp_path/'new.v').write_text('module tt_um_tripwire; RM_IHPSG13_1P_512x16_c2_bm_bist m(); endmodule')
    run=dict(id=39824026639,head_sha='selected',head_branch='main',conclusion='success')
    bound=dict(run_binding=run,source_state='state.json',netlist='new.v',
               files={str(f.relative_to(tmp_path)):hashlib.sha256(f.read_bytes()).hexdigest()
                      for f in (p,tmp_path/'state.json',tmp_path/'new.v')})
    result=base_gl.validate(tmp_path,run,bound=bound,screen_root=newroot)
    assert result['source_run']==39824026639
    assert result['functional_simulation_only'] and not result['official_signoff']
    assert base.review()['run_binding']['id']==39718836864
    (tmp_path/'new.v').write_text('wrong')
    with pytest.raises(ValueError,match='Changed clean'):
        base_gl.validate(tmp_path,run,bound=bound,screen_root=newroot)

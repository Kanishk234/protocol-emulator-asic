import ast
from pathlib import Path
import subprocess

import pytest
import yaml

import wire600_mux_margin_route as route
import wire600_mux_margin_gl as gl
from wire600_mux_margin import REVIEW,validate_change
from wire600_clean_route import validate_bundle
from wire600_extracted_route import profile as prior_profile


def test_new_profile_only_accepts_the_single_mux_clean_source():
    p=route.profile()
    assert p['binding']['run_binding']['id']==39856540600
    assert p['screen_root']==Path('runs/wire600-mux-margin-clean')
    assert p['output']==Path('runs/wire600-mux-margin-route')
    assert p['proposal_review']==REVIEW
    assert p['connectivity_audit'] is validate_change
    assert len(REVIEW['resizes'])==14
    old=prior_profile()['binding'];new=p['binding']
    assert old['files'][old['netlist']]!=new['files'][new['netlist']]
    with pytest.raises(ValueError,match='provenance'):
        validate_bundle(Path('/missing'),old['run_binding'],bound=new,screen_root=p['screen_root'])


def test_both_wrappers_forward_same_frozen_profile(monkeypatch):
    p=route.profile();calls=[]
    monkeypatch.setattr(route.base,'main',lambda p:calls.append(p));route.main()
    assert calls==[p]
    monkeypatch.setattr(gl,'replay_validate',lambda *a,**kw:calls.append((a,kw)))
    gl.validate(Path('/artifact'),{'id':39856540600})
    assert calls[-1]==((Path('/artifact'),{'id':39856540600}),dict(bound=p['binding'],screen_root=p['screen_root']))


@pytest.mark.parametrize('filename',['gds-wire600-mux-margin-route.yaml','l3-wire600-mux-margin-gl.yaml'])
def test_workflows_download_only_selected_source_and_parse(filename):
    root=Path(__file__).resolve().parents[2]
    w=yaml.safe_load((root/'.github/workflows'/filename).read_text());job=next(iter(w['jobs'].values()))
    d=next(s['with'] for s in job['steps'] if 'download-artifact@' in s.get('uses',''))
    assert d['run-id']==39856540600
    assert d['name']=='wire600-mux-margin-clean-evidence-area1-39856540600'
    text='\n'.join(s.get('run','') for s in job['steps'])
    if filename.startswith('l3'):
        assert 'COCOTB_TEST_MODULES=test_l3' in text
        assert 'from wire600_mux_margin_gl import validate' in text
    else:
        assert 'wire600_mux_margin_route.py' in text
        assert job['timeout-minutes']==350
    for s in job['steps']:
        if 'run' not in s:continue
        t=s['run'];subprocess.run(['bash','-n'],input=t,text=True,check=True)
        for marker,end in [("<<'PY'\n",'PY'),("<<'PYCODE'\n",'PYCODE')]:
            if marker in t:ast.parse(t.split(marker,1)[1].split('\n'+end,1)[0])

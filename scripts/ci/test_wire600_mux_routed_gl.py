import ast
import copy
from pathlib import Path
import subprocess

import pytest
import yaml

import wire600_mux_routed_gl as trial
from native_route_gl import validate_electrical


def test_profile_binds_final_route_instead_of_preparation():
    p=trial.PROFILE
    assert p['run_binding']['id']==39868597887
    assert p['run_binding']['conclusion']=='success'
    assert p['source_run']==39856540600
    assert p['route_name']=='wire600-mux-margin-route/qualified-route'
    assert p['netlist_sha256']=='c60823d33a9aa63b20ff4e07a934a4f1daa8b519c4ef2581c9d0b53599f13225'
    assert len(p['files'])==27


def test_missing_evidence_fails_before_replay(tmp_path):
    with pytest.raises(FileNotFoundError):trial.validate(tmp_path,trial.PROFILE['run_binding'])


def test_wrong_final_run_rejected_before_any_files(tmp_path):
    run=copy.deepcopy(trial.PROFILE['run_binding']);run['id']=39856540600
    with pytest.raises(ValueError,match='provenance'):
        validate_electrical(tmp_path,run,trial.PROFILE['netlist_sha256'],profile=trial.PROFILE)


def test_workflow_uses_exact_final_artifact_and_full_suite():
    root=Path(__file__).resolve().parents[2]
    w=yaml.safe_load((root/'.github/workflows/l3-wire600-mux-routed-gl.yaml').read_text())
    job=w['jobs']['l3'];d=next(s['with'] for s in job['steps'] if 'download-artifact@' in s.get('uses',''))
    assert d['run-id']==39868597887
    assert d['name']=='wire600-mux-margin-route-evidence-39868597887'
    text='\n'.join(s.get('run','') for s in job['steps'])
    assert 'COCOTB_TEST_MODULES=test_l3' in text
    assert 'from wire600_mux_routed_gl import validate' in text
    for step in job['steps']:
        if 'run' not in step:continue
        s=step['run'];subprocess.run(['bash','-n'],input=s,text=True,check=True)
        if "<<'PYCODE'\n" in s:ast.parse(s.split("<<'PYCODE'\n",1)[1].split('\nPYCODE',1)[0])

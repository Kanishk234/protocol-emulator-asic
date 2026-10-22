from pathlib import Path
import subprocess

import pytest
import yaml

import wire600_mux_margin as trial
import wire600_extracted_reserve as prior
from wire600_fixed_spef import changed_netlist
from prove_extracted_strengths import prove


def test_only_one_mux_strength_added_to_passing_electrical_profile():
    assert trial.REVIEW['extra_sources']==prior.REVIEW['extra_sources']
    assert trial.REVIEW['resizes'][:-1]==prior.REVIEW['resizes']
    target=trial.REVIEW['resizes'][-1]
    assert target['instance']=='_26761_'
    assert (target['old_master'],target['new_master'])==('sg13cmos5l_mux2_1','sg13cmos5l_mux2_2')
    assert set(target['pins'])=={'A0','A1','S','X'}
    assert trial.REVIEW['diagnostic_resizes']==[target]
    assert trial.REVIEW['evidence_run']==39837795296


def test_explicit_diagnostic_does_not_reapply_prior_sizes():
    target=trial.REVIEW['diagnostic_resizes'][0]
    def ident(n):return '\\'+n+' ' if '[' in n or '.' in n else n
    text=target['old_master']+' '+target['instance']+' ('+','.join('.'+p+'('+ident(n)+')' for p,n in target['pins'].items())+');'
    after=changed_netlist(text,[target])
    assert after==text.replace(target['old_master'],target['new_master'])
    with pytest.raises(ValueError,match='pins'):
        changed_netlist(text.replace('.S('+target['pins']['S']+')','.S(wrong)'),[target])


def test_clean_screen_profile_forwarded(monkeypatch):
    calls=[];monkeypatch.setattr(trial,'screen',lambda **kw:calls.append(kw));trial.main()
    assert calls==[dict(plan_builder=trial.plan,target_emitter=trial.target_call,
                        connectivity_audit=trial.validate_change,
                        output=Path('runs/wire600-mux-margin-clean'))]


def test_single_output_proof_can_have_extra_proven_internal_points(tmp_path,monkeypatch):
    import prove_extracted_strengths as helper
    for c in ('slow_1p08V_125C','typ_1p20V_25C','fast_1p32V_m40C'):
        (tmp_path/('sg13cmos5l_stdcell_'+c+'.lib')).write_text('test library')
    def run(*a,**kw):kw['stdout'].write('Of those cells 5 are proven and 0 are unproven.\nEquivalence successfully proven!\n')
    monkeypatch.setattr(helper.subprocess,'run',run)
    receipt=prove(tmp_path,tmp_path/'out',pairs=[('mux2_1','mux2_2',['A0','A1','S'],'X')])
    assert all(r['proven_outputs']==1 and r['equivalence_points']==5 for r in receipt)
    with pytest.raises(ValueError,match='Missing'):
        prove(tmp_path,tmp_path/'empty',pairs=[])


def test_workflow_keeps_clean_source_and_gates():
    root=Path(__file__).resolve().parents[2]
    old=yaml.safe_load((root/'.github/workflows/gds-wire600-extracted-clean.yaml').read_text())['jobs']['harden']
    new=yaml.safe_load((root/'.github/workflows/gds-wire600-mux-margin-clean.yaml').read_text())['jobs']['harden']
    assert old['env']==new['env']
    assert old['strategy']==new['strategy']
    assert not any('download-artifact@' in s.get('uses','') for s in new['steps'])
    text='\n'.join(s.get('run','') for s in new['steps'])
    assert 'wire600_mux_margin.py' in text
    assert "final < ids.index('OpenROAD.DetailedRouting')" in text
    for step in new['steps']:
        if 'run' in step:subprocess.run(['bash','-n'],input=step['run'],text=True,check=True)

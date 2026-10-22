import copy
from pathlib import Path
import subprocess

import pytest
import yaml

import wire600_extracted_reserve as trial
import wire600_reserve_last as prior
from wire600_fixed_spef import changed_netlist, slack
from wire600_reserve_finish import validate_proposal


def test_exactly_four_new_fanout_sources_and_eleven_strengths():
    old,new=prior.REVIEW,trial.REVIEW
    assert list(new['extra_sources'])[:len(old['extra_sources'])]==list(old['extra_sources'])
    assert {k:new['extra_sources'][k] for k in old['extra_sources']}==old['extra_sources']
    assert set(new['extra_sources'])-set(old['extra_sources'])=={
        'net8721','_21968_','u_chip.g_lane[0].u_slots.wdata_q[13]','net8083'}
    assert new['resizes'][:2]==old['resizes']
    assert len(new['resizes'])==13
    assert {x['instance'] for x in new['resizes'][2:]}=={
        '_38658_','_38755_','place7018','_28099_','_28100_','_28101_','_32036_','place7143','place6382','place6383','_26695_'}
    assert all(not x['old_master'].startswith(('sg13cmos5l_dfr','sg13cmos5l_dlh','sg13cmos5l_lgc'))
               for x in new['resizes'][2:])
    assert '_26693_' not in {x['instance'] for x in new['resizes']}
    with pytest.raises(ValueError,match='Unreviewed'):
        validate_proposal({'groups':[]},new)


def test_fixed_spef_rejects_wrong_master_or_changed_pin():
    cells=[]
    for x in trial.REVIEW['resizes'][2:]:
        ports=','.join('.'+p+'('+n+')' for p,n in x['pins'].items())
        cells.append(x['old_master']+' '+x['instance']+' ('+ports+');')
    text='\n'.join(cells)
    result=changed_netlist(text)
    assert result!=text
    with pytest.raises(ValueError):
        changed_netlist(text.replace('sg13cmos5l_nor3_1','sg13cmos5l_nand3_1',1))
    with pytest.raises(ValueError):
        changed_netlist(text.replace('('+trial.REVIEW['resizes'][2]['pins']['A']+')','(wrong)',1))


def test_missing_or_nonfinite_slack_rejected():
    assert slack(' -0.123456 slack (VIOLATED)\n')==-.123456
    for s in ('','nan slack (MET)','1e999 slack (MET)'):
        with pytest.raises(ValueError):slack(s)


def test_separate_screen_retains_original_source_and_gates():
    root=Path(__file__).resolve().parents[2]
    old=yaml.safe_load((root/'.github/workflows/gds-wire600-clean-reproduction.yaml').read_text())['jobs']['harden']
    new=yaml.safe_load((root/'.github/workflows/gds-wire600-extracted-clean.yaml').read_text())['jobs']['harden']
    assert old['env']==new['env']
    assert old['strategy']==new['strategy']
    assert not any('download-artifact@' in s.get('uses','') for s in new['steps'])
    text='\n'.join(s.get('run','') for s in new['steps'])
    assert 'wire600_extracted_reserve.py' in text
    assert "final < ids.index('OpenROAD.DetailedRouting')" in text
    for step in new['steps']:
        if 'run' in step:subprocess.run(['bash','-n'],input=step['run'],text=True,check=True)


def test_selected_profile_runs_clean_synthesis_with_explicit_callbacks(monkeypatch):
    calls=[]
    monkeypatch.setattr(trial,'screen',lambda **kw:calls.append(kw))
    trial.main()
    assert calls==[dict(plan_builder=trial.plan,target_emitter=trial.target_call,
                        connectivity_audit=trial.validate_change,
                        output=Path('runs/wire600-extracted-clean'))]


def test_missing_fixed_spef_source_stops_before_output(tmp_path):
    from wire600_fixed_spef import diagnose
    with pytest.raises(FileNotFoundError):
        diagnose(tmp_path,tmp_path,tmp_path,tmp_path/'sta',tmp_path/'output')
    assert not (tmp_path/'output').exists()

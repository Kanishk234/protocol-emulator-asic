from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from sa_timing import prepare,replace_cases,validate_parent


def script():
    return ('create_clock -period 20 run\nset p [get_pins -quiet {tile/cfg/Q}]\n'
            'if {[llength $p]!=1} {error "missing configuration pin"}\n'
            'set_case_analysis 0 $p\nincr observed\nreport_checks\n')


def test_candidate_case_identity_and_binary_value_cannot_change():
    for new in ({'other/Q':'1'},{'tile/cfg/Q':'X'}):
        with pytest.raises(ValueError):replace_cases(script(),{'tile/cfg/Q':'0'},new)
    with pytest.raises(ValueError):replace_cases(script(),{'tile/cfg/Q':'1'},{'tile/cfg/Q':'0'})


def test_only_observed_configuration_values_change():
    old=script();new=replace_cases(old,{'tile/cfg/Q':'0'},{'tile/cfg/Q':'1'})
    assert new.replace('set_case_analysis 1 $p','set_case_analysis 0 $p')==old


def test_failed_native_loading_cannot_prepare_candidate_timing(tmp_path):
    (tmp_path/'result.json').write_text('{"passed":false,"cases":{"control":{}}}')
    with pytest.raises(ValueError,match='actual native loading'):
        prepare(None,None,None,None,None,tmp_path,tmp_path/'timing')
    assert not (tmp_path/'timing').exists()


def test_original_extracted_failure_must_reproduce_before_candidate():
    import copy
    control={'diagnostic_complete':True,
             'error':'Configured macro setup/hold or loop-policy check fails',
             'models':{'routed_'+kind:{'worst_slack_ns':slack,'structural_loops':0,
                                       'loop_policy_sensitive':False}
                       for kind,slack in (('setup',-11.108903),('hold',-1.870506))},
             'annotation':{'routed_'+kind+'_'+policy:{'passed':True}
                           for kind in ('setup','hold') for policy in ('static','dynamic')}}
    validate_parent(control)
    changed=copy.deepcopy(control);changed['models']['routed_setup']['worst_slack_ns']=1
    with pytest.raises(ValueError,match='control changed'):validate_parent(changed)
    changed=copy.deepcopy(control);changed['annotation']['routed_hold_dynamic']['passed']=False
    with pytest.raises(ValueError,match='annotation'):validate_parent(changed)
    changed=copy.deepcopy(control);changed['models']['routed_setup']['structural_loops']=1
    with pytest.raises(ValueError,match='control changed'):validate_parent(changed)

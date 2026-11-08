from copy import deepcopy
import json
from pathlib import Path
import pytest
from host_idle_portable_trials import BASE_CONFIG_SHA256, BASE_PROFILE, VARIANTS, select, prepare

ROOT=Path(__file__).resolve().parents[2]


def reference():
    config=json.loads((ROOT/'spikes/phase2_stock_flow/strict_project_config.json').read_text())
    profile=json.loads((ROOT/'spikes/phase2_stock_flow/stock_control_profiles.json').read_text())['profiles'][BASE_PROFILE]
    config.update(profile['changes'])
    selected=dict(profile=BASE_PROFILE,config_sha256=profile['config_sha256'],changes=deepcopy(profile['changes']),
                  rtl_patch='shared_priority',c_select=True,idle_ff=True,host_port_align=True)
    return config,selected


@pytest.mark.parametrize('variant',list(VARIANTS))
def test_exact_source_one_variable_and_fixed_acceptance_inputs(variant):
    config,selected=reference();original=deepcopy((config,selected))
    result,receipt=select(config,selected,variant)
    delta={k:v for k,v in result.items() if config.get(k)!=v}
    assert delta==VARIANTS[variant]
    assert result['CLOCK_PERIOD']==20
    assert result['MACROS']==config['MACROS'] and result['MACROS'] is not config['MACROS']
    assert (config,selected)==original
    assert receipt['comparison_reference_run']==42305323874
    assert receipt['comparison_reference_config_sha256']==BASE_CONFIG_SHA256
    assert receipt['manual_checkpoint_repairs'] is False and receipt['official_gds_signoff'] is False
    assert receipt['hardware_unchanged']==(variant not in ('mode_ff','debug_align'))
    assert all(receipt[k] for k in ('c_select','idle_ff','host_port_align'))


@pytest.mark.parametrize('kind',['wrongclock','differentbase','unknown','missingrtl','wrongprofile'])
def test_unreviewed_trials_or_wrong_source_reject(kind):
    config,selected=reference();variant='late125'
    if kind=='wrongclock':config['CLOCK_PERIOD']=25
    if kind=='differentbase':config['GRT_RESIZER_HOLD_SLACK_MARGIN']=.250
    if kind=='unknown':variant='all_changes'
    if kind=='missingrtl':selected['idle_ff']=False
    if kind=='wrongprofile':selected['profile']='older'
    with pytest.raises(ValueError):select(config,selected,variant)


def test_prepare_only_project_inputs_change(tmp_path):
    config,selected=reference()
    (tmp_path/'src').mkdir();folder=tmp_path/'spikes/phase2_stock_flow';folder.mkdir(parents=True)
    (tmp_path/'src/config.json').write_text(json.dumps(config))
    (tmp_path/'src/trw_chip.v').write_text('untouched source')
    (folder/'selected_profile.json').write_text(json.dumps(selected))
    receipt=prepare(tmp_path,'clock75')
    assert json.loads((tmp_path/'src/config.json').read_text())['CTS_SINK_CLUSTERING_MAX_DIAMETER']==75
    assert (tmp_path/'src/trw_chip.v').read_text()=='untouched source'
    assert json.loads((folder/'selected_profile.json').read_text())==receipt


def test_missing_mode_proof_refuses_before_application(tmp_path):
    config,selected=reference()
    (tmp_path/'src').mkdir();folder=tmp_path/'spikes/phase2_stock_flow';folder.mkdir(parents=True)
    (tmp_path/'src/config.json').write_text(json.dumps(config));(folder/'selected_profile.json').write_text(json.dumps(selected))
    (folder/'mode_ff').mkdir();(folder/'mode_ff/evidence.json').write_text('{"proofs": []}')
    with pytest.raises(ValueError,match='equivalence evidence'):prepare(tmp_path,'mode_ff')


@pytest.mark.parametrize('status,counts',[('pending',(5,0,0)),('passed',(4,1,0)),('passed',(5,0,1)),('passed',(0,0,0))])
def test_source_trials_reject_failed_pending_or_skipped_smokes(status,counts):
    from host_idle_portable_trials import require_smoke
    passed,failed,skipped=counts
    with pytest.raises(ValueError,match='smoke'):
        require_smoke(dict(chip_smoke_status=status,chip_smoke=dict(passed=passed,failed=failed,skipped=skipped)))

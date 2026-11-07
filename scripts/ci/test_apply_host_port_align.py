import difflib
import hashlib
import json
from pathlib import Path

import pytest

from apply_host_port_align import apply


def fixture(tmp_path):
    root=tmp_path/'project';(root/'src').mkdir(parents=True)
    before='module cfg; endmodule\n';after='module cfg; wire q; endmodule\n'
    (root/'src/trw_host.v').write_text(before)
    (root/'src/unrelated.v').write_text('module untouched; endmodule\n')
    evidence=tmp_path/'evidence';evidence.mkdir()
    patch=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),
        fromfile='a/src/trw_host.v',tofile='b/src/trw_host.v'))
    (evidence/'host_port_align.patch').write_text(patch)
    sha=lambda s:hashlib.sha256(s.encode()).hexdigest()
    (evidence/'evidence.json').write_text(json.dumps(dict(reference_sha256=sha(before),
        candidate_sha256=sha(after),patch_sha256=sha(patch))))
    return root,evidence


def test_only_bound_target_changes_and_reapplication_refused(tmp_path):
    root,evidence=fixture(tmp_path)
    receipt=apply(root,evidence)
    assert receipt['changed_files']==['src/trw_host.v']
    assert receipt['before']['src/unrelated.v']==receipt['after']['src/unrelated.v']
    with pytest.raises(ValueError,match='reference source'):apply(root,evidence)


@pytest.mark.parametrize('fault',['source','patch'])
def test_wrong_inputs_fail_before_mutation(tmp_path,fault):
    root,evidence=fixture(tmp_path)
    path=root/'src/trw_host.v' if fault=='source' else evidence/'host_port_align.patch'
    path.write_text(path.read_text()+'// changed\n')
    before=(root/'src/trw_host.v').read_bytes()
    with pytest.raises(ValueError):apply(root,evidence)
    assert (root/'src/trw_host.v').read_bytes()==before


def test_profile_keeps_exact_cselector_physical_recipe():
    root=Path(__file__).resolve().parents[2]
    p=json.loads((root/'spikes/phase2_stock_flow/stock_control_profiles.json').read_text())['profiles']
    old,new=p['rtl_shared_minbuf2_cselect'],p['rtl_shared_minbuf2_host_align']
    assert old['changes']==new['changes'] and old['config_sha256']==new['config_sha256']
    assert new['rtl_patch']==old['rtl_patch'] and new['c_select'] is True and new['host_port_align'] is True


def test_combined_profile_adds_only_idle_storage_to_measured_host_source():
    root=Path(__file__).resolve().parents[2]
    p=json.loads((root/'spikes/phase2_stock_flow/stock_control_profiles.json').read_text())['profiles']
    old,new=p['rtl_shared_minbuf2_host_align'],p['rtl_shared_minbuf2_host_idle_ff']
    assert old['changes']==new['changes'] and old['config_sha256']==new['config_sha256']
    assert new['comparison_reference_run']==42262602008
    assert new['c_select'] is True and new['host_port_align'] is True and new['idle_ff'] is True
    allowed={'idle_ff','comparison_reference_run','comparison_reference_config_sha256'}
    assert {k:v for k,v in new.items() if k not in allowed} == {k:v for k,v in old.items() if k not in allowed}


def test_combined_early_hold_control_is_one_native_target_only():
    root=Path(__file__).resolve().parents[2]
    p=json.loads((root/'spikes/phase2_stock_flow/stock_control_profiles.json').read_text())['profiles']
    old,new=p['rtl_shared_minbuf2_host_idle_ff'],p['rtl_host_idle_early250']
    assert {k:v for k,v in new['changes'].items() if old['changes'].get(k)!=v} == {'PL_RESIZER_HOLD_SLACK_MARGIN':0.25}
    assert set(new['changes']) == set(old['changes'])
    assert new['comparison_reference_run']==42305323874
    assert new['hardware_unchanged'] is True
    assert all(new[k]==old[k] for k in ('rtl_patch','c_select','host_port_align','idle_ff'))
    assert new['changes']['GRT_RESIZER_HOLD_SLACK_MARGIN']==0.175

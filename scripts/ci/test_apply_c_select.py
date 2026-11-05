import json
from pathlib import Path
import shutil

import pytest

from apply_c_select import apply


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'spikes/phase2_stock_flow/pin_input_decode'


def prepared(tmp_path):
    src = tmp_path / 'src'
    src.mkdir()
    shutil.copyfile(ROOT / 'src/trw_pin_io.v', src / 'trw_pin_io.v')
    (src / 'unrelated.v').write_text('module unrelated; endmodule\n')
    return tmp_path


def test_applies_only_bound_selector_and_rejects_reapplication(tmp_path):
    root = prepared(tmp_path)
    result = apply(root, EVIDENCE)
    assert result['changed_files'] == ['src/trw_pin_io.v']
    assert result['before']['src/unrelated.v'] == result['after']['src/unrelated.v']
    with pytest.raises(ValueError, match='reference source'):
        apply(root, EVIDENCE)


def test_wrong_source_is_rejected_before_mutation(tmp_path):
    root = prepared(tmp_path)
    target = root / 'src/trw_pin_io.v'
    target.write_text(target.read_text() + '// changed\n')
    before = target.read_bytes()
    with pytest.raises(ValueError, match='reference source'):
        apply(root, EVIDENCE)
    assert target.read_bytes() == before


def test_changed_patch_is_rejected_before_mutation(tmp_path):
    root = prepared(tmp_path)
    evidence = tmp_path / 'evidence'
    shutil.copytree(EVIDENCE, evidence)
    (evidence / 'c_select_unclamped.patch').write_text('corrupt patch\n')
    before = (root / 'src/trw_pin_io.v').read_bytes()
    with pytest.raises(ValueError, match='patch mismatch'):
        apply(root, evidence)
    assert (root / 'src/trw_pin_io.v').read_bytes() == before


def test_selector_profile_preserves_physical_recipe():
    profiles = json.loads((ROOT / 'spikes/phase2_stock_flow/stock_control_profiles.json').read_text())['profiles']
    base, trial = profiles['rtl_shared_minbuf2'], profiles['rtl_shared_minbuf2_cselect']
    assert trial['changes'] == base['changes']
    assert trial['config_sha256'] == base['config_sha256']
    assert trial['comparison_reference_config_sha256'] == base['config_sha256']
    assert trial['comparison_reference_run'] == 41569397169
    assert trial['rtl_patch'] == base['rtl_patch']
    assert trial['c_select'] is True
    assert trial['hardware_unchanged'] is False

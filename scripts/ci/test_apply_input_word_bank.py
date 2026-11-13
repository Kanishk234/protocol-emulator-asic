from pathlib import Path
import shutil
import subprocess

import pytest

from apply_idle_ff import apply as apply_idle
from apply_input_word_bank import apply

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'spikes/phase2_stock_flow/input_word_bank'


def prepared(tmp_path):
    (tmp_path / 'src').mkdir()
    shutil.copy(ROOT / 'src/trw_pin_cfg.v', tmp_path / 'src/trw_pin_cfg.v')
    (tmp_path / 'src/unrelated.v').write_text('module unchanged; endmodule\n')
    for name in ['verified_design_only', 'mode_predicate', 'config_banks']:
        subprocess.run(['git', 'apply', '--include=src/trw_pin_cfg.v',
                        str(ROOT / f'spikes/phase2_stock_flow/{name}.patch')],
                       cwd=tmp_path, check=True)
    apply_idle(tmp_path, ROOT / 'spikes/phase2_stock_flow/idle_ff')
    return tmp_path


def test_actual_prepared_config_and_single_file_change(tmp_path):
    root = prepared(tmp_path)
    result = apply(root, EVIDENCE)
    assert result['changed_files'] == ['src/trw_pin_cfg.v']
    assert result['before']['src/unrelated.v'] == result['after']['src/unrelated.v']
    assert result['physical_qualified'] is False
    with pytest.raises(ValueError, match='reference source'):
        apply(root, EVIDENCE)


@pytest.mark.parametrize('fault', ['source', 'patch'])
def test_changed_inputs_reject_before_mutation(tmp_path, fault):
    root = prepared(tmp_path)
    evidence = tmp_path / 'evidence'
    shutil.copytree(EVIDENCE, evidence)
    target = root / 'src/trw_pin_cfg.v'
    changed = target if fault == 'source' else evidence / 'input_word_bank.patch'
    changed.write_text(changed.read_text() + '// changed\n')
    before = target.read_bytes()
    with pytest.raises(ValueError):
        apply(root, evidence)
    assert target.read_bytes() == before

import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import pytest
import yaml

from apply_tx_cursor_select import apply

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'spikes/phase2_stock_flow/tx_cursor_select'


def prepared(tmp_path):
    (tmp_path / 'src').mkdir()
    shutil.copy(ROOT / 'src/trw_pin_tx.v', tmp_path / 'src/trw_pin_tx.v')
    (tmp_path / 'src/unrelated.v').write_text('module unchanged; endmodule\n')
    subprocess.run(['git', 'apply', '--include=src/trw_pin_tx.v',
                    str(ROOT / 'spikes/phase2_stock_flow/verified_design_only.patch')],
                   cwd=tmp_path, check=True)
    return tmp_path


def test_exact_prepared_source_and_only_one_file_changes(tmp_path):
    root = prepared(tmp_path)
    result = apply(root, EVIDENCE)
    assert result['changed_files'] == ['src/trw_pin_tx.v']
    assert result['before']['src/unrelated.v'] == result['after']['src/unrelated.v']
    evidence = json.loads((EVIDENCE / 'candidate.json').read_text())
    assert hashlib.sha256((root / 'src/trw_pin_tx.v').read_bytes()).hexdigest() == evidence['candidate_sha256']
    with pytest.raises(ValueError, match='reference source'):
        apply(root, EVIDENCE)


@pytest.mark.parametrize('fault', ['source', 'patch'])
def test_changed_inputs_reject_before_source_mutation(tmp_path, fault):
    root = prepared(tmp_path)
    evidence = tmp_path / 'evidence'
    shutil.copytree(EVIDENCE, evidence)
    target = root / 'src/trw_pin_tx.v'
    changed = target if fault == 'source' else evidence / 'tx_cursor_select.patch'
    changed.write_text(changed.read_text() + '// changed\n')
    before = target.read_bytes()
    with pytest.raises(ValueError):
        apply(root, evidence)
    assert target.read_bytes() == before


def test_screen_keeps_native_runtime_and_acceptance_steps():
    workflows = ROOT / '.github/workflows'
    baseline = yaml.safe_load((workflows / 'gds-official-dev4-drive2-wire175-screen.yaml').read_text())
    trial = yaml.safe_load((workflows / 'gds-official-dev4-tx-cursor-screen.yaml').read_text())
    old_steps = baseline['jobs']['screen']['steps']
    new_steps = trial['jobs']['screen']['steps']
    assert len(old_steps) == len(new_steps)
    for old, new in zip(old_steps, new_steps):
        if old['name'] == 'Select bounded native wire175 trial':
            assert 'apply_tx_cursor_select.py' in new['run']
            assert "assert e['protocol_replay']['passed']==22" in new['run']
            assert 'drive2_wire175.py' not in new['run']
        elif old.get('uses', '').startswith('actions/upload-artifact'):
            assert old['uses'] == new['uses'] and new['if'] == 'always()'
            assert 'runs/tx_cursor_select/**' in new['with']['path']
        else:
            assert old == new, old['name']
    assert trial['jobs']['screen']['env'] == baseline['jobs']['screen']['env']
    assert trial['jobs']['screen']['timeout-minutes'] == baseline['jobs']['screen']['timeout-minutes']

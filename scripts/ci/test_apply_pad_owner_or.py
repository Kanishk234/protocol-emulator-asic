from pathlib import Path
import shutil
import subprocess

import pytest
import yaml

from apply_pad_owner_or import apply

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'spikes/phase2_stock_flow/pad_owner_or'


def prepared(tmp_path):
    (tmp_path / 'src').mkdir()
    shutil.copy(ROOT / 'src/trw_pins.v', tmp_path / 'src/trw_pins.v')
    (tmp_path / 'src/unrelated.v').write_text('module unchanged; endmodule\n')
    return tmp_path


def test_verified_patch_changes_only_pins_and_rejects_reapplication(tmp_path):
    root = prepared(tmp_path)
    result = apply(root, EVIDENCE)
    assert result['changed_files'] == ['src/trw_pins.v']
    assert result['before']['src/unrelated.v'] == result['after']['src/unrelated.v']
    with pytest.raises(ValueError, match='reference source'):
        apply(root, EVIDENCE)


@pytest.mark.parametrize('fault', ['source', 'patch'])
def test_invalid_input_rejects_before_mutation(tmp_path, fault):
    root = prepared(tmp_path)
    evidence = tmp_path / 'evidence'
    shutil.copytree(EVIDENCE, evidence)
    target = root / 'src/trw_pins.v'
    path = target if fault == 'source' else evidence / 'pad_owner_or.patch'
    path.write_text(path.read_text() + '// changed\n')
    before = target.read_bytes()
    with pytest.raises(ValueError):
        apply(root, evidence)
    assert target.read_bytes() == before


def test_manual_screen_preserves_native_runtime_and_acceptance_gates():
    folder = ROOT / '.github/workflows'
    old = yaml.safe_load((folder / 'gds-official-dev4-pending-polarity-screen.yaml').read_text())
    new = yaml.safe_load((folder / 'gds-official-dev4-pad-owner-screen.yaml').read_text())
    assert new['on'] == {'workflow_dispatch': {}}
    assert old['jobs']['screen']['env'] == new['jobs']['screen']['env']
    steps = new['jobs']['screen']['steps']
    extra = [s for s in steps if s['name'] == 'Apply verified pad-owner OR candidate']
    assert len(extra) == 1
    assert "e['protocol_replay']['passed']==22" in extra[0]['run']
    assert "e['reference_config_sha256']" in extra[0]['run']
    rest = [s for s in steps if s not in extra]
    assert len(rest) == len(old['jobs']['screen']['steps'])
    for a, b in zip(old['jobs']['screen']['steps'], rest):
        if a.get('uses', '').startswith('actions/upload-artifact'):
            assert a['uses'] == b['uses'] and b['if'] == 'always()'
            assert b['with']['path'].startswith(a['with']['path'])
        else:
            assert a == b, a['name']
    for s in steps:
        if 'run' in s:
            subprocess.run(['bash', '-n'], input=s['run'], text=True, check=True)

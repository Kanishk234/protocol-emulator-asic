from pathlib import Path
import shutil
import subprocess

import pytest
import yaml

from apply_pending_drop_polarity import apply

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'spikes/phase2_stock_flow/pending_drop_polarity'


def prepared(tmp_path):
    (tmp_path / 'src').mkdir()
    shutil.copy(ROOT / 'src/trw_chan_port.v', tmp_path / 'src/trw_chan_port.v')
    (tmp_path / 'src/unrelated.v').write_text('module unchanged; endmodule\n')
    for name in ['verified_design_only', 'late_drop_select', 'forwarded_drop']:
        subprocess.run(['git', 'apply', '--include=src/trw_chan_port.v',
                        str(ROOT / f'spikes/phase2_stock_flow/{name}.patch')],
                       cwd=tmp_path, check=True)
    return tmp_path


def test_actual_reference_changes_only_port(tmp_path):
    root = prepared(tmp_path)
    result = apply(root, EVIDENCE)
    assert result['changed_files'] == ['src/trw_chan_port.v']
    assert result['before']['src/unrelated.v'] == result['after']['src/unrelated.v']
    with pytest.raises(ValueError, match='reference source'):
        apply(root, EVIDENCE)


@pytest.mark.parametrize('fault', ['source', 'patch'])
def test_invalid_input_rejects_before_mutation(tmp_path, fault):
    root = prepared(tmp_path)
    evidence = tmp_path / 'evidence'
    shutil.copytree(EVIDENCE, evidence)
    target = root / 'src/trw_chan_port.v'
    path = target if fault == 'source' else evidence / 'pending_drop_polarity.patch'
    path.write_text(path.read_text() + '// changed\n')
    before = target.read_bytes()
    with pytest.raises(ValueError):
        apply(root, evidence)
    assert target.read_bytes() == before


def test_native_runtime_and_gates_are_identical():
    workflows = ROOT / '.github/workflows'
    old = yaml.safe_load((workflows / 'gds-official-dev4-tx-cursor-screen.yaml').read_text())
    new = yaml.safe_load((workflows / 'gds-official-dev4-pending-polarity-screen.yaml').read_text())
    before = old['jobs']['screen']['steps']
    after = new['jobs']['screen']['steps']
    extra = [s for s in after if s['name'] == 'Apply verified pending-event polarity candidate']
    assert len(extra) == 1 and "e['protocol_replay']['passed']==22" in extra[0]['run']
    after = [s for s in after if s not in extra]
    assert len(before) == len(after)
    for a, b in zip(before, after):
        if a.get('uses', '').startswith('actions/upload-artifact'):
            assert a['uses'] == b['uses'] and b['if'] == 'always()'
            assert 'runs/pending_drop_polarity/**' in b['with']['path']
        else:
            assert a == b, a['name']
    assert old['jobs']['screen']['env'] == new['jobs']['screen']['env']

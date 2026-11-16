import difflib
import hashlib
import json
from pathlib import Path
import subprocess

import pytest
import yaml

from apply_level_cache import apply

ROOT = Path(__file__).resolve().parents[2]


def fixture(tmp_path):
    source = tmp_path / 'src'
    source.mkdir()
    evidence = tmp_path / 'evidence'
    evidence.mkdir()
    sha = lambda data: hashlib.sha256(data).hexdigest()
    old, new, patch = {}, {}, ''
    for name in ('trw_chip.v', 'trw_pin_unit.v', 'trw_pin_tx.v', 'trw_pin_bs.v'):
        before, after = '// fixture before\n', '// fixture after\n'
        (source / name).write_text(before)
        old[name], new[name] = sha(before.encode()), sha(after.encode())
        patch += ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                            fromfile='a/src/' + name, tofile='b/src/' + name))
    (source / 'trw_pin_cfg.v').write_text('clock contract fixture\n')
    (source / 'config.json').write_text('{"CLOCK_PERIOD":20}\n')
    (evidence / 'level_cache.patch').write_text(patch)
    manifest = dict(reference_files=old, candidate_files=new, patch_sha256=sha(patch.encode()),
                    configuration_source_sha256=sha((source / 'trw_pin_cfg.v').read_bytes()),
                    reference_config_sha256=sha((source / 'config.json').read_bytes()))
    (evidence / 'candidate.json').write_text(json.dumps(manifest))
    return evidence


def test_patch_preserves_config_and_rejects_reapplication(tmp_path):
    evidence = fixture(tmp_path)
    result = apply(tmp_path, evidence)
    assert len(result['changed_files']) == 4 and not result['physical_qualified']
    assert result['before']['src/config.json'] == result['after']['src/config.json']
    with pytest.raises(ValueError, match='reference source'):
        apply(tmp_path, evidence)


@pytest.mark.parametrize('name', ['trw_chip.v', 'trw_pin_cfg.v', 'config.json'])
def test_source_clock_contract_and_physical_drift_reject_before_mutation(tmp_path, name):
    evidence = fixture(tmp_path)
    path = tmp_path / 'src' / name
    path.write_text(path.read_text() + '// drift\n')
    before = {p.name: p.read_bytes() for p in (tmp_path / 'src').iterdir()}
    with pytest.raises(ValueError):
        apply(tmp_path, evidence)
    assert before == {p.name: p.read_bytes() for p in (tmp_path / 'src').iterdir()}


def test_screen_keeps_native_controls_and_final_gates():
    folder = ROOT / '.github/workflows'
    old = yaml.safe_load((folder / 'gds-official-dev4-pad-owner-screen.yaml').read_text())
    new = yaml.safe_load((folder / 'gds-official-dev4-level-cache-screen.yaml').read_text())
    assert new['on'] == {'workflow_dispatch': {}}
    assert old['jobs']['screen']['env'] == new['jobs']['screen']['env']
    steps = new['jobs']['screen']['steps']
    extra = [s for s in steps if s['name'] == 'Apply verified same-edge output cache']
    assert len(extra) == 1
    assert "e['protocol_replay']['passed']==22" in extra[0]['run']
    assert "e['top_port_phase_replay']['passed']==5" in extra[0]['run']
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
    text = extra[0]['run'].split("<<'PYCODE'\n")[1].rsplit('\nPYCODE', 1)[0]
    compile(text, '<level-cache-workflow>', 'exec')


def test_no_owner_screen_preserves_pending_controls_and_guards_source():
    folder = ROOT / '.github/workflows'
    old = yaml.safe_load((folder / 'gds-official-dev4-pending-polarity-screen.yaml').read_text())
    new = yaml.safe_load((folder / 'gds-official-dev4-cache-no-owner-screen.yaml').read_text())
    assert new['on'] == {'workflow_dispatch': {}}
    assert old['jobs']['screen']['env'] == new['jobs']['screen']['env']
    steps = new['jobs']['screen']['steps']
    extra = [s for s in steps if s['name'] == 'Apply output cache on pre-owner baseline']
    assert len(extra) == 1
    assert "e['pad_mux_sha256']" in extra[0]['run']
    assert "e['protocol_replay']['passed']==22" in extra[0]['run']
    assert "e['top_port_phase_replay']['passed']==5" in extra[0]['run']
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
    script = extra[0]['run'].split("<<'PYCODE'\n")[1].rsplit('\nPYCODE', 1)[0]
    compile(script, '<cache-no-owner-workflow>', 'exec')

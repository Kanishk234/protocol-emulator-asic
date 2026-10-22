import ast
from pathlib import Path
import subprocess

import pytest
import yaml

import wire600_clean_reproduction as trial


def test_refuses_existing_source_or_download_receipt(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path/'runs/native-stock-screen').mkdir(parents=True)
    with pytest.raises(ValueError, match='absent source'):
        trial.require_empty_source()


@pytest.mark.parametrize('message', ['runner crashed', 'Missing fresh electrical checks',
                                    'Native setup reserve screen fails; no detailed routing'])
def test_never_swallows_other_failures(tmp_path, monkeypatch, message):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(trial, 'require_empty_source', lambda: None)
    monkeypatch.setattr(trial, 'clean_screen', lambda: (_ for _ in ()).throw(ValueError(message)))
    monkeypatch.setattr(trial, 'repair_screen', lambda **kw: pytest.fail('Unexpected repair'))
    with pytest.raises(ValueError, match=message):
        trial.main()
    assert not (trial.OUTPUT/'source_reproduction.json').exists()


def test_expected_control_rejection_still_requires_exact_hashes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(trial, 'require_empty_source', lambda: None)
    monkeypatch.setattr(trial, 'clean_screen', lambda: (_ for _ in ()).throw(ValueError(trial.EXPECTED_REJECTION)))
    monkeypatch.setattr(trial, 'repair_screen', lambda **kw: pytest.fail('Unexpected repair'))
    with pytest.raises(FileNotFoundError):
        trial.main()
    assert not (trial.OUTPUT/'source_reproduction.json').exists()


def test_requires_fresh_synthesis_and_forbids_detailed_route(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls = []
    monkeypatch.setattr(trial, 'validate_files', lambda root: calls.append(root))
    with pytest.raises(ValueError, match='fresh synthesis'):
        trial.validate_clean_source()
    stage = tmp_path/'runs/native-stock-screen/flow/7-yosys-synthesis'
    stage.mkdir(parents=True)
    (stage/'state_out.json').write_text('{}')
    trial.validate_clean_source()
    (stage.parent/'50-openroad-detailedrouting').mkdir()
    with pytest.raises(ValueError, match='Detailed routing'):
        trial.validate_clean_source()
    assert len(calls) == 3


def test_workflow_has_no_checkpoint_download_or_drt_and_parses():
    root = Path(__file__).resolve().parents[2]
    old = yaml.safe_load((root/'.github/workflows/gds-native-delta8-wire600-screen.yaml').read_text())['jobs']['harden']
    new = yaml.safe_load((root/'.github/workflows/gds-wire600-clean-reproduction.yaml').read_text())['jobs']['harden']
    assert old['env'] == new['env']
    assert old['strategy'] == new['strategy']
    assert not any('download-artifact' in s.get('uses', '') for s in new['steps'])
    text = '\n'.join(s.get('run', '') for s in new['steps'])
    assert 'wire600_clean_reproduction.py' in text
    assert "final < ids.index('OpenROAD.DetailedRouting')" in text
    for step in new['steps']:
        if 'run' not in step:
            continue
        script = step['run']
        subprocess.run(['bash', '-n'], input=script, text=True, check=True)
        if "<<'PY'\n" in script:
            ast.parse(script.split("<<'PY'\n", 1)[1].split('\nPY', 1)[0])

from pathlib import Path
import subprocess

import pytest
import verify_cached_port_select as trial


def test_real_all_legal_source_counts_prove(tmp_path):
    receipt = trial.verify(tmp_path/'candidate')
    assert [row['sources'] for row in receipt['proofs']] == list(range(1, 17))
    assert all(row['reference_points'] > 0 and row['cached_points'] > 0 for row in receipt['proofs'])
    assert receipt['physical_timing_proven'] is False


def test_full_patch_and_workflow_bind_all_verified_modules(tmp_path):
    import yaml
    from timing_trial import PATCHES
    from verify_arithmetic_trial import verify as prepare_tx
    from verify_timing_trial import verify
    output = tmp_path/'candidate'
    prepare_tx('tx-late-cursor', output)
    subprocess.run(['git', 'apply', str(trial.ROOT/'spikes/r4_floorplan/cached_port_select.patch')],
                   cwd=output, check=True)
    variant = 'bs-resync-cfg-tx-cached-select'
    patch, files = PATCHES[variant]
    subprocess.run(['git', 'apply', '--reverse', '--check',
                    str(trial.ROOT/'spikes/r4_floorplan'/patch)], cwd=output, check=True)
    workflow = trial.ROOT/'.github/workflows/gds-native-cached-select-setup-reserve-screen.yaml'
    job = yaml.safe_load(workflow.read_text())['jobs']['harden']
    assert job['env']['VARIANT'] == variant
    commands = '\n'.join(step.get('run', '') for step in job['steps'])
    for file in files:
        assert trial.digest(output/file) in commands
    assert 'native_cached_select_screen.py' in commands
    assert 'float(cfg["CLOCK_PERIOD"]) == 20.0' in commands
    with pytest.raises(ValueError, match='clocked-host'):
        verify(variant, tmp_path/'wrong-verifier')


def test_native_wrapper_requires_exact_source_and_unchanged_policy(monkeypatch):
    import native_cached_select_screen as screen
    calls = []
    monkeypatch.setattr(screen, 'reserve_screen', lambda **kw: calls.append(kw))
    monkeypatch.setenv('VARIANT', 'bs-resync-cfg-tx-cursor')
    with pytest.raises(ValueError): screen.main()
    monkeypatch.setenv('VARIANT', 'bs-resync-cfg-tx-cached-select')
    screen.main()
    assert calls == [{'config_transform': screen.configure}]


def test_wrong_named_reference_source_rejected():
    with pytest.raises(ValueError): trial.named_reference('unreviewed source')


def test_wrong_configuration_sampling_enable_fails_real_proof(tmp_path):
    # Reuse the actual source module, not a behavioral mirror of the cache.
    original = subprocess.check_output(['git', 'show', '3393eea:src/trw_chan_port.v'], text=True)
    (tmp_path/'src').mkdir()
    defs = subprocess.check_output(['git', 'show', '3393eea:src/trw_assert.vh'], text=True)
    (tmp_path/'src/trw_assert.vh').write_text(defs)
    (tmp_path/'src/trw_chan_port.v').write_text(original)
    subprocess.run(['git', 'apply', str(trial.ROOT/'spikes/r4_floorplan/cached_port_select.patch')],
                   cwd=tmp_path, check=True, capture_output=True)
    candidate = tmp_path/'src/trw_chan_port.v'
    text = candidate.read_text()
    assert text.count('else if (cfg_we)\n            for (sm') == 1
    candidate.write_text(text.replace('else if (cfg_we)\n            for (sm',
                                     'else if (!cfg_we)\n            for (sm'))
    (tmp_path/'gold.v').write_text(trial.named_reference(original))
    with pytest.raises(subprocess.CalledProcessError):
        trial.prove(tmp_path, 'gold.v', 'src/trw_chan_port.v', 6, 'mutant')

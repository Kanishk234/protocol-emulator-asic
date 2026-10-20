from pathlib import Path
import subprocess

import pytest
import verify_arithmetic_trial as trial
import native_arithmetic_screen as screen


@pytest.mark.parametrize('variant', ['sample-csa', 'tx-late-cursor'])
def test_real_delta_proves_against_exact_combined_source(tmp_path, variant):
    receipt = trial.verify(variant, tmp_path / 'candidate')
    assert receipt['equivalence_points'] > 0
    assert receipt['source_sha256'] == trial.TRIALS[variant][3]
    assert receipt['physical_timing_proven'] is False


@pytest.mark.parametrize('short,variant,filename', [
    ('tx-late-cursor', 'bs-resync-cfg-tx-cursor', 'gds-native-tx-cursor-setup-reserve-screen.yaml')])
def test_workflow_and_full_patch_bind_verified_delta(tmp_path, short, variant, filename):
    import yaml
    from timing_trial import PATCHES
    from verify_timing_trial import verify
    output = trial.prepare_combined(tmp_path / 'candidate', trial.BASE_VARIANT)
    trial.apply_delta(output, short)
    patch, names = PATCHES[variant]
    subprocess.run(['git', 'apply', '--reverse', '--check',
                    str(trial.ROOT / 'spikes/r4_floorplan' / patch)], cwd=output,
                   check=True, capture_output=True, timeout=30)
    job = yaml.safe_load((trial.ROOT / '.github/workflows' / filename).read_text())['jobs']['harden']
    assert job['env']['VARIANT'] == variant
    commands = '\n'.join(step.get('run', '') for step in job['steps'])
    for name in ('trw_pin_bs.v', 'trw_pin_cfg.v', 'trw_pin_tx.v'):
        assert trial.digest(output / 'src' / name) in commands
    assert 'native_arithmetic_screen.py' in commands
    assert 'float(cfg["CLOCK_PERIOD"]) == 20.0' in commands
    assert 'total-timeout 6900' in commands
    with pytest.raises(ValueError, match='clocked-host'):
        verify(variant, tmp_path / 'wrong-model')


def test_screen_refuses_unknown_variants_and_keeps_policy(monkeypatch):
    calls = []
    monkeypatch.setattr(screen, 'reserve_screen', lambda **kw: calls.append(kw))
    monkeypatch.setenv('VARIANT', trial.BASE_VARIANT)
    with pytest.raises(ValueError):
        screen.main()
    for variant in screen.VARIANTS:
        monkeypatch.setenv('VARIANT', variant)
        screen.main()
    assert calls == [{'config_transform': screen.configure}]


def test_unknown_trial_rejected_before_preparing_files(tmp_path):
    with pytest.raises(ValueError, match='Unknown'):
        trial.verify('unreviewed', tmp_path / 'candidate')
    assert not (tmp_path / 'candidate').exists()


def test_wrong_base_rejected_before_mutation(tmp_path):
    (tmp_path / 'src').mkdir()
    source = tmp_path / 'src/trw_pin_bs.v'
    source.write_text('wrong source')
    with pytest.raises(ValueError, match='Wrong measured'):
        trial.apply_delta(tmp_path, 'sample-csa')
    assert source.read_text() == 'wrong source'
    assert not (tmp_path / 'arithmetic_gold.v').exists()


def test_extra_source_edit_is_rejected(tmp_path, monkeypatch):
    output = trial.prepare_combined(tmp_path / 'candidate', trial.BASE_VARIANT)
    original = subprocess.run
    def run(*args, **kwargs):
        result = original(*args, **kwargs)
        with (output / 'src/trw_pin_tx.v').open('a') as stream:
            stream.write('\n// unexpected extra source edit\n')
        return result
    monkeypatch.setattr(trial.subprocess, 'run', run)
    with pytest.raises(ValueError, match='unexpected source'):
        trial.apply_delta(output, 'sample-csa')


def test_missing_twos_complement_carry_fails_equivalence(tmp_path):
    output = trial.prepare_combined(tmp_path / 'candidate', trial.BASE_VARIANT)
    source = trial.apply_delta(output, 'sample-csa')
    text = source.read_text()
    assert "sample_carry | 25'd1" in text
    source.write_text(text.replace("sample_carry | 25'd1", 'sample_carry'))
    script = '''read_verilog -DSYNTHESIS -Isrc arithmetic_gold.v
rename trw_pin_bs gold
read_verilog -DSYNTHESIS -Isrc src/trw_pin_bs.v
rename trw_pin_bs gate
proc
memory
opt
equiv_make gold gate equiv
hierarchy -top equiv
equiv_simple
equiv_induct -seq 2
equiv_status -assert
'''
    (output / 'mutant.ys').write_text(script)
    result = subprocess.run(['yosys', '-Q', '-s', 'mutant.ys'], cwd=output,
                            capture_output=True, text=True, timeout=180)
    assert result.returncode != 0
    assert 'unproven' in result.stdout + result.stderr

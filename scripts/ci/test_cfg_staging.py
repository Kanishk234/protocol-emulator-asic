"""Real negative controls for banked staging's phase/reset/carrier checks."""
from pathlib import Path
import shutil
import subprocess

import pytest
import verify_cfg_staging as target
from verify_timing_trial import verify
import native_cfg_staging_screen as screen
import native_resync_cfg_staging_screen as combined_screen


@pytest.fixture(scope='module')
def prepared(tmp_path_factory):
    return target.prepare(tmp_path_factory.mktemp('cfg-stage') / 'trial')


@pytest.mark.parametrize('mutation', ['wrong-enable', 'wrong-edge', 'carrier-disabled'])
def test_phase_comparator_rejects_regressions(prepared, tmp_path, mutation):
    shutil.copytree(prepared / 'src', tmp_path / 'src')
    gold = (prepared / 'gold_trw_pin_cfg.v').read_text()
    gate = (prepared / 'src/trw_pin_cfg.v').read_text()
    if mutation == 'wrong-enable':
        assert 'else if (we)\n            wdata_q' in gate
        gate = gate.replace('else if (we)\n            wdata_q', 'else if (!we)\n            wdata_q')
    elif mutation == 'wrong-edge':
        start = gate.index('    reg [15:0] wdata_q;')
        gate = gate[:start] + gate[start:].replace('always @(posedge clk)', 'always @(negedge clk)', 1)
    else:
        assert 'assign carrier_active = active_q;' in gate
        gate = gate.replace('assign carrier_active = active_q;', "assign carrier_active = 1'b0;")
    for kind, source in [('gold', gold), ('gate', gate)]:
        (tmp_path / (kind + '.v')).write_text(source.replace('module trw_pin_cfg #(', f'module trw_pin_cfg_{kind} #(', 1))
    subprocess.run(['iverilog', '-g2005', '-Isrc', '-s', 'tb_cfg_staging',
                    '-Ptb_cfg_staging.FULL=1', '-o', 'check.vvp', 'gold.v', 'gate.v',
                    str(target.ROOT / 'test_internal/cfg_staging/tb_cfg_staging.v')],
                   cwd=tmp_path, check=True, capture_output=True, timeout=30)
    result = subprocess.run(['vvp', 'check.vvp'], cwd=tmp_path,
                            text=True, capture_output=True, timeout=30)
    assert result.returncode != 0 and 'Configuration staging changes observable phase behavior' in result.stdout


@pytest.mark.parametrize('variant', target.VARIANTS)
def test_generic_verifier_does_not_use_wrong_clock_model(tmp_path, variant):
    with pytest.raises(ValueError, match='clocked-host'):
        verify(variant, tmp_path / 'trial')
    assert not (tmp_path / 'trial').exists()


@pytest.mark.parametrize('runner,variant', [(screen, target.VARIANT), (combined_screen, target.VARIANTS[1])])
def test_screen_keeps_existing_policy_and_requires_reviewed_variant(monkeypatch, runner, variant):
    calls = []
    monkeypatch.setattr(runner, 'reserve_screen', lambda **kw: calls.append(kw))
    monkeypatch.setenv('VARIANT', 'bs-resync-event')
    with pytest.raises(ValueError):
        runner.main()
    monkeypatch.setenv('VARIANT', variant)
    runner.main()
    from native_wire150_screen import configure
    assert calls == [{'config_transform': configure}]


@pytest.mark.parametrize('variant,filename', [
    (target.VARIANT, 'gds-native-cfg-staging-setup-reserve-screen.yaml'),
    (target.VARIANTS[1], 'gds-native-resync-cfg-staging-setup-reserve-screen.yaml')])
def test_workflow_binds_both_rtl_hashes_and_same_clock(variant, filename):
    import hashlib
    import yaml
    path = target.ROOT / '.github/workflows' / filename
    job = yaml.safe_load(path.read_text())['jobs']['harden']
    assert job['env']['VARIANT'] == variant
    assert job['env']['CANDIDATE_SHA'] == target.CANDIDATE
    commands = '\n'.join(step.get('run', '') for step in job['steps'])
    assert ('native_resync_cfg_staging_screen.py' if variant == target.VARIANTS[1] else 'native_cfg_staging_screen.py') in commands
    assert 'float(cfg["CLOCK_PERIOD"]) == 20.0' in commands
    assert 'timing_trial.py' in commands
    # prepare() and hash checks bind the exact archived source plus reviewed patch.
    import tempfile
    with tempfile.TemporaryDirectory() as temporary:
        output = target.prepare(Path(temporary) / 'trial', variant)
        for name in ('trw_pin_cfg.v', 'trw_pin_bs.v'):
            assert hashlib.sha256((output / 'src' / name).read_bytes()).hexdigest() in commands


def test_combination_preserves_verified_configuration_source(prepared, tmp_path):
    combined = target.prepare(tmp_path / 'trial', target.VARIANTS[1])
    assert (combined / 'src/trw_pin_cfg.v').read_bytes() == (prepared / 'src/trw_pin_cfg.v').read_bytes()
    assert (combined / 'src/trw_pin_bs.v').read_bytes() != (prepared / 'src/trw_pin_bs.v').read_bytes()


def test_prepare_rejects_unreviewed_source_before_mutation(tmp_path):
    with pytest.raises(ValueError, match='Unreviewed'):
        target.prepare(tmp_path / 'trial', 'unknown')
    assert not (tmp_path / 'trial').exists()

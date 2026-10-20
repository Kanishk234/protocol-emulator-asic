"""Real negative controls for banked staging's phase/reset/carrier checks."""
from pathlib import Path
import shutil
import subprocess

import pytest
import verify_cfg_staging as target
from verify_timing_trial import verify
import native_cfg_staging_screen as screen


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


def test_generic_verifier_does_not_use_wrong_clock_model(tmp_path):
    with pytest.raises(ValueError, match='clocked-host'):
        verify(target.VARIANT, tmp_path / 'trial')
    assert not (tmp_path / 'trial').exists()


def test_screen_keeps_existing_policy_and_requires_reviewed_variant(monkeypatch):
    calls = []
    monkeypatch.setattr(screen, 'reserve_screen', lambda **kw: calls.append(kw))
    monkeypatch.setenv('VARIANT', 'bs-resync-event')
    with pytest.raises(ValueError):
        screen.main()
    monkeypatch.setenv('VARIANT', target.VARIANT)
    screen.main()
    from native_wire150_screen import configure
    assert calls == [{'config_transform': configure}]


def test_workflow_binds_both_rtl_hashes_and_same_clock():
    import hashlib
    import yaml
    path = target.ROOT / '.github/workflows/gds-native-cfg-staging-setup-reserve-screen.yaml'
    job = yaml.safe_load(path.read_text())['jobs']['harden']
    assert job['env']['VARIANT'] == target.VARIANT
    assert job['env']['CANDIDATE_SHA'] == target.CANDIDATE
    commands = '\n'.join(step.get('run', '') for step in job['steps'])
    assert 'native_cfg_staging_screen.py' in commands
    assert 'float(cfg["CLOCK_PERIOD"]) == 20.0' in commands
    assert 'timing_trial.py' in commands
    # prepare() and hash checks bind the exact archived source plus reviewed patch.
    import tempfile
    with tempfile.TemporaryDirectory() as temporary:
        output = target.prepare(Path(temporary) / 'trial')
        for name in ('trw_pin_cfg.v', 'trw_pin_bs.v'):
            assert hashlib.sha256((output / 'src' / name).read_bytes()).hexdigest() in commands

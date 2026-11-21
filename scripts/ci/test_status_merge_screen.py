"""Meaningful fail-closed checks for the candidate's pre-routing acceptance gates."""
import math
from pathlib import Path
import sys

import pytest

CI = Path(__file__).resolve().parent
sys.path.insert(0, str(CI))
import status_merge_screen as screen


def passing(corner):
    metrics = {}
    for kind in ('setup', 'hold'):
        metrics[f'timing__{kind}__ws__corner:{corner}'] = 0 if kind == 'setup' else 0.15
        metrics[f'timing__{kind}_vio__count__corner:{corner}'] = 0
    for kind in ('slew', 'cap', 'fanout'):
        metrics[f'design__max_{kind}_violation__count__corner:{corner}'] = 0
    return metrics, {'worst_reported_setup_slack_ns': 0.163304}


@pytest.mark.parametrize('corner', screen.CORNERS)
def test_zero_aggregate_setup_requires_positive_functional_reserve(corner):
    metrics, functional = passing(corner)
    assert screen.qualify_corner(metrics, functional, corner) == []
    functional['worst_reported_setup_slack_ns'] = 0
    assert screen.qualify_corner(metrics, functional, corner)


def test_fast_hold_acceptance_is_50ps_not_rounded_zero():
    corner = screen.CORNERS[0]
    metrics, functional = passing(corner)
    metrics[f'timing__hold__ws__corner:{corner}'] = 0.049999
    assert screen.qualify_corner(metrics, functional, corner)
    metrics[f'timing__hold__ws__corner:{corner}'] = 0.05
    assert not screen.qualify_corner(metrics, functional, corner)


@pytest.mark.parametrize('kind', ['setup', 'hold', 'slew', 'cap', 'fanout'])
def test_nonzero_violation_fails_even_with_positive_slack(kind):
    corner = screen.CORNERS[0]
    metrics, functional = passing(corner)
    key = (f'timing__{kind}_vio__count__corner:{corner}' if kind in ('setup', 'hold')
           else f'design__max_{kind}_violation__count__corner:{corner}')
    metrics[key] = 1
    assert screen.qualify_corner(metrics, functional, corner)


@pytest.mark.parametrize('bad', [None, math.nan, math.inf, True])
def test_missing_or_nonfinite_slack_never_passes(bad):
    corner = screen.CORNERS[0]
    metrics, functional = passing(corner)
    metrics[f'timing__setup__ws__corner:{corner}'] = bad
    with pytest.raises(ValueError):
        screen.qualify_corner(metrics, functional, corner)


def test_staging_preserves_main_and_rejects_modified_trial_config(tmp_path):
    before = screen.inventory(screen.ROOT)
    design = tmp_path / 'design'
    screen.prepare(design)
    bound = screen.check_inputs(design)
    assert screen.inventory(screen.ROOT) == before
    assert bound['candidate_inputs'] == {**before, 'src/trw_pin_bs.v': screen.load(
        screen.ROOT / 'docs/reports/phase3_status_merge_candidate_result.json')['candidate_sha256']}
    config = design / 'src/config.json'
    config.write_text(config.read_text() + ' ')
    with pytest.raises(ValueError, match='Changed candidate input'):
        screen.check_inputs(design)
    with pytest.raises(ValueError, match='already exists'):
        screen.prepare(design)


def test_workflow_support_tools_pin_matches_validator():
    import yaml
    workflow = yaml.safe_load((screen.ROOT / '.github/workflows/status-merge-screen.yaml').read_text())
    steps = workflow['jobs']['screen']['steps']
    checkout = [s for s in steps if s.get('with', {}).get('repository') == 'TinyTapeout/tt-support-tools']
    assert len(checkout) == 1 and checkout[0]['with']['ref'] == screen.TOOLS


def test_signoff_audit_uses_stock_base_instead_of_missing_generated_file(tmp_path):
    path = screen.stock_signoff(tmp_path, {'FALLBACK_SDC': '/pinned/scripts/base.sdc'})
    assert path.read_text() == 'source $::env(SCRIPTS_DIR)/base.sdc\n'
    for key in ('PNR_SDC_FILE', 'SIGNOFF_SDC_FILE'):
        with pytest.raises(ValueError, match='Unexpected explicit'):
            screen.stock_signoff(tmp_path, {'FALLBACK_SDC': '/pinned/scripts/base.sdc', key: '/custom.sdc'})
    with pytest.raises(ValueError, match='fallback'):
        screen.stock_signoff(tmp_path, {'FALLBACK_SDC': '/custom.sdc'})


def test_diagnostic_configs_preserve_source_relative_path_resolution(tmp_path):
    (tmp_path / 'src').mkdir()
    config = {'VERILOG_FILES': ['dir::tt_um_tripwire.v'], 'CLOCK_PERIOD': 20}
    path = screen.diagnostic_config(tmp_path, 'one-corner', config)
    assert path.parent == tmp_path / 'src'
    assert screen.load(path) == config


def test_staging_cannot_recurse_into_qualified_source():
    with pytest.raises(ValueError, match='outside qualified'):
        screen.prepare(screen.ROOT / 'src' / 'trial')


def test_root_mode_adds_only_verified_config_rtl(tmp_path):
    reference = tmp_path / 'reference'
    root_mode = tmp_path / 'root-mode'
    screen.prepare(reference)
    screen.prepare(root_mode, variant='root-mode')
    reference_receipt = screen.check_inputs(reference)
    root_receipt = screen.check_inputs(root_mode)
    assert reference_receipt['variant'] == 'status-merge'
    assert root_receipt['variant'] == 'root-mode'
    assert root_receipt['candidate_inputs'] == {
        **reference_receipt['candidate_inputs'],
        'src/trw_pin_cfg.v': '02a63f1d46ad7360a0f9a8a56b004478b629540ce4eb25234235b7b4b9c43581',
    }


def test_fanout7_stages_only_the_config_override(tmp_path):
    reference = tmp_path / 'root-mode'
    trial = tmp_path / 'root-mode-fanout7'
    screen.prepare(reference, variant='root-mode')
    screen.prepare(trial, variant='root-mode-fanout7')
    reference_inputs = screen.check_inputs(reference)['candidate_inputs']
    trial_inputs = screen.check_inputs(trial)['candidate_inputs']
    assert {name for name in reference_inputs if reference_inputs[name] != trial_inputs[name]} == {
        'src/config.json'
    }
    assert screen.load(trial / 'src/config.json') == {
        **screen.load(reference / 'src/config.json'),
        'MAX_FANOUT_CONSTRAINT': 7,
    }


def test_b_edge_synthesis_trial_changes_only_two_pin_rtl_files(tmp_path):
    base = tmp_path / 'root-mode-synth'
    trial = tmp_path / 'root-mode-b-edge-synth'
    screen.prepare(base, variant=base.name)
    screen.prepare(trial, variant=trial.name)
    before = screen.check_inputs(base)['candidate_inputs']
    after = screen.check_inputs(trial)['candidate_inputs']
    assert before.keys() == after.keys()
    assert {name for name in before if before[name] != after[name]} == {
        'src/trw_pin_rx.v', 'src/trw_pin_unit.v'
    }
    physical = tmp_path / 'root-mode-b-edge'
    screen.prepare(physical, variant=physical.name)
    assert screen.check_inputs(physical)['candidate_inputs'] == after

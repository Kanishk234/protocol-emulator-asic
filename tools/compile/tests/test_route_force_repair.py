"""Fail-closed custom-router checkpoint and final evidence tests; no local EDA."""
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'test_internal'))
import cloud_route_force_repair as force


def test_force_runs_only_after_both_same_process_identity_hash_gates():
    text = force.force_trace(True)
    assert text.count('log_cmd global_route {*}$arg_list') == 1
    assert text.count('log_cmd grt::force_reroute_pair {*}$warp_handles') == 1
    for expected in (force.EXPECTED_SEGMENTS, force.EXPECTED_GRID):
        assert text.index(expected) < text.index('log_cmd grt::force_reroute_pair')
    assert text.index('initial-grid.tsv') < text.index('log_cmd grt::force_reroute_pair')
    assert text.index('before-census.tsv') < text.index('log_cmd grt::force_reroute_pair') < text.index('after-census.tsv')
    assert 'return -options $warp_route_options $warp_route_error' in text
    assert '-allow_congestion' not in text
    assert 'set_nets_to_route' not in text
    assert 'set warp_handles {}' in text
    assert 'cell_pad[31] cell_val[30]' in text


def test_default_identity_contains_no_repair():
    text = force.force_trace(False)
    assert 'force_reroute_pair' not in text
    assert force.EXPECTED_GRID in text and force.EXPECTED_SEGMENTS in text
    assert 'native-return.txt' in text


@pytest.mark.parametrize('value', [None, 1, 'yes', []])
def test_ambiguous_repair_mode_rejected(value):
    with pytest.raises(ValueError):
        force.force_trace(value)


def test_geometry_export_retains_obstructions_boundary_shapes_and_all_instance_locations():
    text = force.geometry_body('before-geometry.tsv')
    assert 'getObstructions' in text and 'getBPins' in text and 'getBBox' in text
    assert 'read_db' not in text and 'write_def' not in text
    assert '$::env(STEP_DIR)/before-geometry.tsv' in text


@pytest.fixture
def stage(tmp_path, monkeypatch):
    for name in ('initial-segments.txt', 'native-segments.txt', 'initial-grid.tsv', 'native-grid.tsv'):
        (tmp_path/name).write_text('fixture')
    for kind in ('census', 'geometry'):
        (tmp_path/f'before-{kind}.tsv').write_text('same')
        (tmp_path/f'after-{kind}.tsv').write_text('same')
    (tmp_path/'native-return.txt').write_text('1\nGRT-0232 failed\n')
    (tmp_path/'openroad-globalrouting.log').write_text('initial121table\n'+force.MARKER+'\nno final table')
    data = {'final_overflow': 119, 'missing': ['some_net'], 'table': None}
    monkeypatch.setattr(force.trace.cfg, 'sha', lambda p: force.EXPECTED_SEGMENTS if 'segments' in p.name else force.EXPECTED_GRID)
    monkeypatch.setattr(force, 'audit', lambda p: {'total_overflow': 121 if p.name.startswith('initial') else data['final_overflow'], 'sha256': force.EXPECTED_GRID})
    monkeypatch.setattr(force, 'capacities', lambda p: ('same', {}))
    monkeypatch.setattr(force, 'net_names', lambda p: list(range(3659)))
    monkeypatch.setattr(force, 'guide_coverage', lambda *a: {'missing_guides': data['missing']})
    def table(raw):
        if force.MARKER in raw:
            pytest.fail('Must not parse initial table as final')
        if data['table'] is None:
            raise ValueError('No final table')
        return data['table']
    monkeypatch.setattr(force.trace.routing, 'parse_congestion', table)
    return tmp_path, data


def test_232_failure_grid_is_not_claimed_as_initial_table_or_pass(stage):
    path, _ = stage
    result = force.validate_stage(path, True)
    assert result['final_grid']['total_overflow'] == 119
    assert not result['final_table_available']
    assert not result['native_repair_passed']
    assert not result['physical_acceptance']


def test_success_requires_actual_final_table_and_guides(stage):
    path, data = stage
    (path/'native-return.txt').write_text('0\n')
    data['final_overflow'] = 0
    with pytest.raises(ValueError, match='lacks final table'):
        force.validate_stage(path, True)
    data['table'] = [{'total_overflow': 0}]
    with pytest.raises(ValueError, match='complete guides'):
        force.validate_stage(path, True)
    data['missing'] = []
    result = force.validate_stage(path, True)
    assert result['native_repair_passed'] and not result['physical_acceptance']


def test_native_success_with_nonzero_grid_rejected(stage):
    path, _ = stage
    (path/'native-return.txt').write_text('0\n')
    with pytest.raises(ValueError, match='contradicts grid'):
        force.validate_stage(path, True)


def test_geometry_change_rejects_even_lower_overflow(stage):
    path, _ = stage
    (path/'after-geometry.tsv').write_text('moved')
    with pytest.raises(ValueError, match='physical geometry'):
        force.validate_stage(path, True)


def test_capacity_change_rejected(stage, monkeypatch):
    path, _ = stage
    monkeypatch.setattr(force, 'capacities', lambda p: p.name)
    with pytest.raises(ValueError, match='capacity arrays'):
        force.validate_stage(path, True)


def test_final_table_contradiction_rejected(stage):
    path, data = stage
    data['table'] = [{'total_overflow': 121}]
    with pytest.raises(ValueError, match='contradicts final grid'):
        force.validate_stage(path, True)


def test_changed_complete_net_census_rejected(stage, monkeypatch):
    path, _ = stage
    monkeypatch.setattr(force, 'net_names', lambda p: list(range(3659 if p.name.startswith('initial') else 3658)))
    with pytest.raises(ValueError, match='net census changed'):
        force.validate_stage(path, True)


@pytest.mark.parametrize('binary', ['/tmp/openroad', '/nix/store/short-openroad/bin/openroad', '/nix/store/'+'a'*32+'-openroad/bin/sh'])
def test_binary_override_rejects_uncontrolled_paths(binary):
    with pytest.raises(ValueError):
        force.docker_options(binary)

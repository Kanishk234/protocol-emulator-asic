"""Fail-closed custom-router checkpoint and final evidence tests; no local EDA."""
from pathlib import Path
import re
import sys
from types import SimpleNamespace
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'test_internal'))
import cloud_route_force_repair as force


def test_boundary_directions_match_independent_pinned_cmos5l_lef_extract():
    # Verbatim layer/direction statements from sg13cmos5l_tech.lef at PDK
    # 2bbec755dc67ca3db0261c3d6163e15735d66710, lines73/75,116/118,
    # 158/160,200/202. Full file SHA256:
    # 3edd5a1ad31e8307be537d0d1b85c3258fefeb21aac04aaa476e4f72de4cffd5.
    lef_extract = '''LAYER Metal1
  TYPE ROUTING ;
  DIRECTION HORIZONTAL ;
LAYER Metal2
  TYPE ROUTING ;
  DIRECTION VERTICAL ;
LAYER Metal3
  TYPE ROUTING ;
  DIRECTION HORIZONTAL ;
LAYER Metal4
  TYPE ROUTING ;
  DIRECTION VERTICAL ;
'''
    actual = {layer: direction[0] for layer, direction in
              re.findall(r'LAYER (Metal[1-4])\s+TYPE ROUTING ;\s+DIRECTION (HORIZONTAL|VERTICAL) ;', lef_extract)}
    assert actual == force.BOUNDARY_DIRECTIONS


def boundary_text(nx=3, ny=3, extra_usage=0):
    rows = [f'META\t{nx}\t{ny}']
    for layer, direction in force.BOUNDARY_DIRECTIONS.items():
        positions = ((x, ny-1) for x in range(nx-1)) if direction == 'H' else ((nx-1, y) for y in range(ny-1))
        for index, (x, y) in enumerate(positions):
            rows.append(f'EDGE\t{layer}\t{direction}\t{x}\t{y}\t10\t{10+extra_usage if layer == "Metal1" and index == 0 else 0}')
    return '\n'.join(rows)+'\n'


def test_runtime_mounts_add_individual_outputs_without_hiding_container_store(monkeypatch):
    root = '/nix/store/' + 'a'*32 + '-openroad'
    dependency = '/nix/store/' + 'b'*32 + '-runtime'
    monkeypatch.setattr(force.Path, 'is_file', lambda self: True)
    monkeypatch.setattr(force.Path, 'exists', lambda self: True)
    def query(command, **kwargs):
        assert command == ['nix-store', '--query', '--requisites', root]
        return SimpleNamespace(stdout=root+'\n'+dependency+'\n')
    monkeypatch.setattr(force.subprocess, 'run', query)
    options = force.docker_options(root+'/bin/openroad')
    force.trace.validate_execution_options('cloud_route_force_repair.py', options, ('GRT-0116',), False)
    assert '/nix/store:/nix/store:ro' not in options
    assert root+':'+root+':ro' in options
    assert dependency+':'+dependency+':ro' in options


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
    for name in ('initial-boundary-grid.tsv', 'native-boundary-grid.tsv'):
        (tmp_path/name).write_text(boundary_text())
    monkeypatch.setattr(force.trace.cfg, 'sha', lambda p: force.EXPECTED_SEGMENTS if 'segments' in p.name else force.EXPECTED_GRID)
    monkeypatch.setattr(force, 'audit', lambda p: {'total_overflow': 121 if p.name.startswith('initial') else data['final_overflow'], 'sha256': force.EXPECTED_GRID, 'dimensions': [3, 3]})
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


def test_real_boundary_grid_has_complete_directional_edges(tmp_path):
    path = tmp_path/'boundary.tsv'
    path.write_text(boundary_text(4, 3, extra_usage=2))
    result = force.audit_boundary_grid(path)
    assert result['observed_edges'] == 2*(4-1)+2*(3-1)
    assert result['total_overflow'] == 2
    assert result['overflow_by_layer']['Metal1'] == 2


@pytest.mark.parametrize('corrupt', ['missing', 'duplicate', 'negative', 'wrong_direction', 'wrong_boundary', 'bad_dimensions'])
def test_boundary_grid_rejects_malformed_or_incomplete_census(tmp_path, corrupt):
    path = tmp_path/'boundary.tsv'
    rows = boundary_text().splitlines()
    if corrupt == 'missing':
        rows.pop()
    elif corrupt == 'duplicate':
        rows.append(rows[-1])
    elif corrupt == 'negative':
        rows[1] = rows[1].rsplit('\t', 1)[0]+'\t-1'
    elif corrupt == 'wrong_direction':
        fields = rows[1].split('\t')
        fields[2] = 'V'
        rows[1] = '\t'.join(fields)
    elif corrupt == 'wrong_boundary':
        fields = rows[1].split('\t')
        fields[4] = '0'
        rows[1] = '\t'.join(fields)
    else:
        rows[0] = 'META\t1\t3'
    path.write_text('\n'.join(rows)+'\n')
    with pytest.raises(ValueError):
        force.audit_boundary_grid(path)


def test_boundary_capacity_change_rejected_even_when_interior_is_identical(stage):
    path, _ = stage
    file = path/'native-boundary-grid.tsv'
    file.write_text(file.read_text().replace('\t10\t', '\t11\t', 1))
    with pytest.raises(ValueError, match='boundary capacity arrays'):
        force.validate_stage(path, True)


def test_boundary_overflow_prevents_false_zero_interior_success(stage):
    path, data = stage
    data['final_overflow'] = 0
    (path/'native-return.txt').write_text('0\n')
    (path/'native-boundary-grid.tsv').write_text(boundary_text(extra_usage=1))
    with pytest.raises(ValueError, match='contradicts grid'):
        force.validate_stage(path, True)


def test_table_reconciles_boundary_plus_interior_overflow(stage):
    path, data = stage
    (path/'native-boundary-grid.tsv').write_text(boundary_text(extra_usage=2))
    data['table'] = [{'total_overflow': 121}]
    result = force.validate_stage(path, True)
    assert result['final_observed_full_grid_overflow'] == 121
    assert result['final_boundary_grid']['total_overflow'] == 2
    data['table'] = [{'total_overflow': 119}]
    with pytest.raises(ValueError, match='contradicts final grid'):
        force.validate_stage(path, True)


def test_sidecar_preserves_legacy_export_and_omits_display_sentinels():
    text = force.boundary_grid_body('initial-boundary-grid.tsv')
    assert '[llength $warp_y]-1' in text and '[llength $warp_x]-1' in text
    assert 'getDirection' in text and 'Metal1 HORIZONTAL' in text
    assert '\\tH\\t' in text and '\\tV\\t' in text
    combined = force.force_trace(True)
    assert combined.index('initial-boundary-grid.tsv') < combined.index('log_cmd grt::force_reroute_pair')
    assert combined.index('native-boundary-grid.tsv') > combined.index('log_cmd grt::force_reroute_pair')
    assert force.grid_body('initial-grid.tsv') in combined


def test_boundary_tcl_exports_actual_complete_sidecar(tmp_path):
    tkinter = pytest.importorskip('tkinter')
    interp = tkinter.Tcl()
    interp.setvar('env(STEP_DIR)', str(tmp_path))
    interp.eval('''
        namespace eval ord {proc get_db {} {return warp_db}}
        proc warp_db {method args} {return warp_tech}
        proc warp_tech {method args} {return {Metal1 Metal2 Metal3 Metal4}}
        proc Metal1 {method args} {if {$method eq "getName"} {return Metal1}; return HORIZONTAL}
        proc Metal2 {method args} {if {$method eq "getName"} {return Metal2}; return VERTICAL}
        proc Metal3 {method args} {if {$method eq "getName"} {return Metal3}; return HORIZONTAL}
        proc Metal4 {method args} {if {$method eq "getName"} {return Metal4}; return VERTICAL}
        proc warp_grid_command {method args} {
            if {$method eq "getCapacity"} {return 10}
            if {$method eq "getUsage"} {return 0}
            error "Unexpected grid method"
        }
        set warp_grid warp_grid_command
        set warp_x {0 7200 14400 21600}
        set warp_y {0 7200 14400}
    ''')
    interp.eval(force.boundary_grid_body('native-boundary-grid.tsv'))
    data = force.audit_boundary_grid(tmp_path/'native-boundary-grid.tsv')
    assert data['dimensions'] == [4, 3] and data['observed_edges'] == 10
    assert data['total_overflow'] == 0
    interp.eval('proc Metal1 {method args} {if {$method eq "getName"} {return Metal1}; return VERTICAL}')
    with pytest.raises(tkinter.TclError, match='differs from pinned CMOS5L'):
        interp.eval(force.boundary_grid_body('rejected-boundary-grid.tsv'))


def test_changed_complete_net_census_rejected(stage, monkeypatch):
    path, _ = stage
    monkeypatch.setattr(force, 'net_names', lambda p: list(range(3659 if p.name.startswith('initial') else 3658)))
    with pytest.raises(ValueError, match='net census changed'):
        force.validate_stage(path, True)


@pytest.mark.parametrize('binary', ['/tmp/openroad', '/nix/store/short-openroad/bin/openroad', '/nix/store/'+'a'*32+'-openroad/bin/sh'])
def test_binary_override_rejects_uncontrolled_paths(binary):
    with pytest.raises(ValueError):
        force.docker_options(binary)

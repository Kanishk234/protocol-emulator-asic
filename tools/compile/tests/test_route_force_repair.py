"""Fail-closed custom-router checkpoint and final evidence tests; no local EDA."""
from pathlib import Path
import re
import sys
from types import SimpleNamespace
import pytest
import hashlib

sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'test_internal'))
import cloud_route_force_repair as force


@pytest.fixture
def corridor_controls(tmp_path, monkeypatch):
    stages, cases, calls = {}, {}, []
    for name, overflow in [('default_identity', 121), ('forced_pair', 132), ('rebuilt_pair', 139)]:
        stage = tmp_path/name/'replay'/'1-openroad-globalrouting';stage.mkdir(parents=True)
        stages[name] = stage
        witnesses=[]
        for phase in ('initial', 'final'):
            directory=stage/('corridor-'+phase);directory.mkdir()
            path=directory/'native-corridor.tsv';path.write_text('native-fixture\n')
            witnesses.append('WARP_NATIVE_CORRIDOR_COMPLETE path='+str(path))
        (stage/'openroad-globalrouting.log').write_text('\n'.join(witnesses)+'\n')
        for filename in ('native-segments.txt','native-grid.tsv','native-boundary-grid.tsv'):
            (stage/filename).write_text('unchanged')
        cases[name]={'native_tcl_returncode':1,'native_error':'GRT-0116' if name=='default_identity' else 'GRT-0232',
            'final_observed_full_grid_overflow':overflow,'capacities_unchanged':True,
            'physical_census_and_geometry_unchanged':True,'physical_acceptance':False,
            'final_boundary_grid':{'total_overflow':0},
            'final_grid':{'layers':{k:{'overflow':v} for k,v in {'Metal1':15,'Metal2':66,'Metal3':26,'Metal4':32}.items()}}}
    def sha(path):
        path=Path(path)
        keys={'native-segments.txt':'segments','native-grid.tsv':'interior','native-boundary-grid.tsv':'boundary'}
        if path.name in keys and 'default_identity' in path.parts and path.read_text()=='unchanged':
            return force.EXPECTED_SEGMENTS if path.name=='native-segments.txt' else force.EXPECTED_GRID
        if path.name in keys and path.read_text()=='unchanged':return force.REFERENCE_REBUILT[keys[path.name]]
        return hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr(force.trace.cfg,'sha',sha)
    monkeypatch.setattr(force,'validate_observer',lambda *args:calls.append('legacy-qualified'))
    def parse(path):
        calls.append(('parse',Path(path)))
        return {'model_gate':'PASS','input_sha256':sha(path),'native_inputs_authenticated':False,'physical_acceptance':False}
    monkeypatch.setattr(force,'native_corridor_audit',parse)
    return stages,cases,calls


def test_native_corridor_all_controls_qualified_before_any_parser(corridor_controls):
    stages,cases,calls=corridor_controls
    result=force.qualify_native_corridors(stages,cases)
    assert calls[0]=='legacy-qualified' and len(calls)==7
    assert result['controls_qualified'] and result['model_gate']
    assert not result['native_inputs_authenticated'] and not result['physical_acceptance']


@pytest.mark.parametrize('failure',['missing_case','wrong_default','changed121','changed139','wrong_native_error','geometry'])
def test_failed_control_prevents_raw_native_interpretation(corridor_controls,failure):
    stages,cases,calls=corridor_controls
    if failure=='missing_case':cases.pop('default_identity')
    elif failure=='wrong_default':cases['default_identity']['final_observed_full_grid_overflow']=120
    elif failure=='changed121':(stages['default_identity']/'native-grid.tsv').write_text('changed')
    elif failure=='changed139':(stages['rebuilt_pair']/'native-grid.tsv').write_text('changed')
    elif failure=='wrong_native_error':cases['rebuilt_pair']['native_error']='Unexpected exporter error'
    else:cases['forced_pair']['physical_census_and_geometry_unchanged']=False
    with pytest.raises(ValueError):force.qualify_native_corridors(stages,cases)
    assert not any(isinstance(call,tuple) and call[0]=='parse' for call in calls)


@pytest.mark.parametrize('failure',['missing_witness','duplicate_witness','reversed_witness','wrong_path','missing_file'])
def test_failed_native_export_or_witness_prevents_parsing(corridor_controls,failure):
    stages,cases,calls=corridor_controls;stage=stages['rebuilt_pair'];log=stage/'openroad-globalrouting.log'
    rows=log.read_text().splitlines()
    if failure=='missing_witness':rows.pop()
    elif failure=='duplicate_witness':rows.append(rows[-1])
    elif failure=='reversed_witness':rows.reverse()
    elif failure=='wrong_path':rows[-1]=rows[-1].replace('/corridor-final/','/corridor-other/')
    else:(stage/'corridor-final/native-corridor.tsv').unlink()
    log.write_text('\n'.join(rows)+'\n')
    with pytest.raises(ValueError):force.qualify_native_corridors(stages,cases)
    assert not any(isinstance(call,tuple) and call[0]=='parse' for call in calls)


def test_native_ledger_mismatch_is_diagnostic_not_fabricated_success(corridor_controls,monkeypatch):
    stages,cases,_=corridor_controls
    monkeypatch.setattr(force,'native_corridor_audit',lambda p:{'model_gate':'FAIL','input_sha256':force.trace.cfg.sha(p),'usage_ledger_reconciled':False,
        'native_inputs_authenticated':False,'physical_acceptance':False})
    result=force.qualify_native_corridors(stages,cases)
    assert result['controls_qualified'] and result['model_gate'] is False
    assert not result['physical_acceptance']


def test_malformed_native_state_is_collection_error(corridor_controls,monkeypatch):
    stages,cases,_=corridor_controls
    def malformed(path):raise ValueError('Malformed native ledger')
    monkeypatch.setattr(force,'native_corridor_audit',malformed)
    with pytest.raises(ValueError,match='Malformed native'):force.qualify_native_corridors(stages,cases)


def test_corridor_initial_export_follows_exact_and_physical_guards():
    text=force.force_trace(True,True)
    for expected in [force.EXPECTED_GRID,force.EXPECTED_SEGMENTS,*force.BEFORE_PHYSICAL.values()]:
        assert text.index(expected)<text.index('set warp_corridor_dir $::env(STEP_DIR)/corridor-initial')
    assert text.index('corridor-initial')<text.index('log_cmd grt::force_reroute_pair')<text.index('corridor-final')
    assert text.count('log_cmd grt::export_native_corridor_state')==2


def test_failed_native_export_unsets_environment_and_preserves_error(tmp_path):
    tkinter=pytest.importorskip('tkinter');interp=tkinter.Tcl()
    interp.setvar('env(STEP_DIR)',str(tmp_path))
    interp.eval('''namespace eval grt {proc export_native_corridor_state {} {
        set out [open $::env(WARP_CORRIDOR_DIR)/native-corridor.tsv w]
        puts $out partial
        close $out
        file attributes $::env(WARP_CORRIDOR_DIR)/native-corridor.tsv -permissions 0600
        error "Native writer failed"
    }}''')
    interp.eval('proc log_cmd {args} {uplevel 1 $args}')
    with pytest.raises(tkinter.TclError,match='Native writer failed'):
        interp.eval(force.corridor_export_body('initial'))
    assert interp.eval('info exists ::env(WARP_CORRIDOR_DIR)')=='0'
    partial=tmp_path/'corridor-initial/native-corridor.tsv'
    assert partial.read_text()=='partial\n'
    assert partial.stat().st_mode & 0o777==0o600


def test_successful_native_export_changes_only_known_owner_only_artifact_to_readable(tmp_path):
    tkinter=pytest.importorskip('tkinter');interp=tkinter.Tcl()
    interp.setvar('env(STEP_DIR)',str(tmp_path))
    unrelated=tmp_path/'unrelated.tsv';unrelated.write_text('private');unrelated.chmod(0o600)
    interp.eval('''namespace eval grt {proc export_native_corridor_state {} {
        set out [open $::env(WARP_CORRIDOR_DIR)/native-corridor.tsv w]
        puts $out complete
        close $out
        file attributes $::env(WARP_CORRIDOR_DIR)/native-corridor.tsv -permissions 0600
    }}''')
    interp.eval('proc log_cmd {args} {uplevel 1 $args}')
    interp.eval(force.corridor_export_body('initial'))
    output=tmp_path/'corridor-initial/native-corridor.tsv'
    assert output.read_text()=='complete\n' and output.stat().st_mode & 0o777==0o644
    assert unrelated.stat().st_mode & 0o777==0o600
    assert interp.eval('info exists ::env(WARP_CORRIDOR_DIR)')=='0'


def test_native_export_rejects_symlink_before_permission_change(tmp_path):
    tkinter=pytest.importorskip('tkinter');interp=tkinter.Tcl()
    interp.setvar('env(STEP_DIR)',str(tmp_path))
    target=tmp_path/'private.tsv';target.write_text('private');target.chmod(0o600)
    interp.setvar('warp_test_target',str(target))
    interp.eval('''namespace eval grt {proc export_native_corridor_state {} {
        file link -symbolic $::env(WARP_CORRIDOR_DIR)/native-corridor.tsv $::warp_test_target
    }}''')
    interp.eval('proc log_cmd {args} {uplevel 1 $args}')
    with pytest.raises(tkinter.TclError,match='not a regular file'):
        interp.eval(force.corridor_export_body('initial'))
    assert target.stat().st_mode & 0o777==0o600
    assert interp.eval('info exists ::env(WARP_CORRIDOR_DIR)')=='0'


def test_native_export_rejects_existing_directory_without_calling_writer(tmp_path):
    tkinter=pytest.importorskip('tkinter');interp=tkinter.Tcl()
    interp.setvar('env(STEP_DIR)',str(tmp_path));(tmp_path/'corridor-initial').mkdir()
    interp.eval('namespace eval grt {proc export_native_corridor_state {} {error "Writer must not execute"}}')
    interp.eval('proc log_cmd {args} {uplevel 1 $args}')
    with pytest.raises(tkinter.TclError,match='already exists'):
        interp.eval(force.corridor_export_body('initial'))


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


def test_boundary_accepts_actual_native_integral_decimal_format(tmp_path):
    # Hosted38853662972 emitted: EDGE Metal1 H 0 97 29.0 12.0.
    # Keep its measured resource spellings in a small complete grid fixture.
    path = tmp_path/'boundary.tsv'
    rows = boundary_text().splitlines()
    fields = rows[1].split('\t')
    fields[-2:] = ['29.0', '12.0']
    rows[1] = '\t'.join(fields)
    path.write_text('\n'.join(rows)+'\n')
    result = force.audit_boundary_grid(path)
    assert result['capacities'][('Metal1', 'H', 0, 2)] == 29
    assert result['total_overflow'] == 0


@pytest.mark.parametrize('invalid', ['-1.0', 'NaN', 'Infinity', '-Infinity', '1.5', 'not-a-number'])
@pytest.mark.parametrize('field', [-2, -1])
def test_boundary_rejects_invalid_resource_numbers(tmp_path, invalid, field):
    path = tmp_path/'boundary.tsv'
    rows = boundary_text().splitlines()
    fields = rows[1].split('\t')
    fields[field] = invalid
    rows[1] = '\t'.join(fields)
    path.write_text('\n'.join(rows)+'\n')
    with pytest.raises(ValueError):
        force.audit_boundary_grid(path)


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


def test_observer_is_enabled_only_inside_the_caught_force_call():
    text = force.force_trace(True)
    assert text.index('initial-grid.tsv') < text.index('set ::env(WARP_FORCE_OBSERVER_DIR)')
    assert text.index('set ::env(WARP_FORCE_OBSERVER_DIR)') < text.index('catch {log_cmd grt::force_reroute_pair')
    assert text.index('catch {log_cmd grt::force_reroute_pair') < text.index('unset ::env(WARP_FORCE_OBSERVER_DIR)')
    assert 'WARP_FORCE_OBSERVER_DIR' not in force.force_trace(False)


def test_observer_names_reject_invented_members_and_wrong_added_count(tmp_path):
    path = tmp_path/'names.tsv'
    path.write_text('META\t0\t2\t2\nNET\tcell_pad[31]\t1\nNET\tcell_val[30]\t1\n')
    names, added = force.parse_observer_names(path, 0, set(), force.SEEDS)
    assert names == added == force.SEEDS
    path.write_text(path.read_text().replace('2\t2', '2\t1'))
    with pytest.raises(ValueError, match='count/order'):
        force.parse_observer_names(path, 0, set(), force.SEEDS)
    path.write_text('META\t0\t2\t2\nNET\tcell_pad[31]\t1\nNET\tunknown\t1\n')
    with pytest.raises(ValueError, match='unknown identity'):
        force.parse_observer_names(path, 0, set(), force.SEEDS)


@pytest.fixture
def observer(tmp_path, monkeypatch):
    import hashlib
    names = sorted(force.SEEDS | {'cell_pad[27]', 'cell_val[27]'} | {f'net{i}' for i in range(3655)})
    route = ''.join(name+'\n(\n3600 3600 Metal1 10800 3600 Metal1\n)\n' for name in names)
    def grid():
        text = 'META\t3\t3\nX\t0 7200 14400\nY\t0 7200 14400\n'
        for layer, over in [('Metal1', 15), ('Metal2', 52), ('Metal3', 24), ('Metal4', 41)]:
            for x in range(2):
                for y in range(2):
                    text += f'CELL\t{layer}\t{x}\t{y}\t17.0\t{17+over if x==y==0 else 0}.0\n'
        return text
    for name in ('initial-segments.txt', 'native-segments.txt'):
        (tmp_path/name).write_text(route)
    for name in ('initial-grid.tsv', 'native-grid.tsv'):
        (tmp_path/name).write_text(grid())
    for name in ('initial-boundary-grid.tsv', 'native-boundary-grid.tsv'):
        (tmp_path/name).write_text(boundary_text())
    directory = tmp_path/'force-observer'; directory.mkdir()
    previous, log = set(), force.MARKER+'\n'
    for index in range(5):
        current = force.SEEDS | set(names[:index])
        added = current-previous
        prefix = directory/f'pass_{index}'
        (directory/f'pass_{index}.nets.tsv').write_text(f'META\t{index}\t{len(current)}\t{len(added)}\n'+
            ''.join(f'NET\t{name}\t{int(name not in previous)}\n' for name in sorted(current)))
        for suffix, content in [('native-grid.tsv', grid()), ('boundary-native-grid.tsv', boundary_text()), ('segments.txt', route)]:
            (directory/f'pass_{index}.{suffix}').write_text(content)
        log += f'WARP_FORCE_OBSERVER pass={index} nets={len(current)} added={len(added)} segment_bytes={len(route.encode())} interior_grid=true boundary_preferred=true prefix={prefix}\n'
        previous = current
    (tmp_path/'openroad-globalrouting.log').write_text(log)
    original_sha = force.trace.cfg.sha
    def identity(path):
        if path.parent == tmp_path:
            values = {'native-segments.txt': 'segments', 'native-grid.tsv': 'interior', 'native-boundary-grid.tsv': 'boundary'}
            if path.name in values:
                return force.REFERENCE_REPAIR[values[path.name]]
        return original_sha(path)
    monkeypatch.setattr(force.trace.cfg, 'sha', identity)
    validated = {'native_tcl_returncode': 1, 'native_error': 'GRT-0232 failed',
        'final_observed_full_grid_overflow': 132, 'final_boundary_grid': {'total_overflow': 0},
        'final_grid': {'layers': {name: {'overflow': value} for name,value in
            [('Metal1',15),('Metal2',52),('Metal3',24),('Metal4',41)]}},
        'guide_coverage': {'required_net_count': 3691, 'missing_guides': sorted(force.SEEDS)}}
    return tmp_path, validated


def test_observer_validates_all_five_complete_snapshots_after_reference_gate(observer):
    stage, data = observer
    result = force.validate_observer(stage, data)
    assert result['observer_equivalence_verified'] and len(result['passes']) == 5
    assert not result['physical_acceptance'] and not result['routing_improvement']
    assert all(row['observed_full_grid_overflow'] == 132 for row in result['passes'])


def test_observer_rejects_changed_final_reference_before_interpretation(observer, monkeypatch):
    stage, data = observer
    monkeypatch.setattr(force.trace.cfg, 'sha', lambda path: 'wrong')
    with pytest.raises(ValueError, match='changes measured132'):
        force.validate_observer(stage, data)


@pytest.mark.parametrize('corruption', ['missing', 'extra', 'linked', 'census', 'capacity', 'usage', 'bytes', 'witness'])
def test_observer_corruption_rejected(observer, corruption):
    stage, data = observer
    directory = stage/'force-observer'
    if corruption == 'missing':
        (directory/'pass_2.nets.tsv').unlink()
    elif corruption == 'extra':
        (directory/'unrecognized').write_text('extra')
    elif corruption == 'linked':
        path = directory/'pass_0.nets.tsv'
        text = path.read_text(); path.unlink()
        other = stage/'names-copy'; other.write_text(text); path.symlink_to(other)
    elif corruption == 'census':
        path = directory/'pass_3.segments.txt'; path.write_text('cell_pad[31]\n(\n3600 3600 Metal1 10800 3600 Metal1\n)\n')
    elif corruption in ('capacity', 'usage'):
        path = directory/('pass_1.native-grid.tsv' if corruption=='capacity' else 'pass_4.native-grid.tsv')
        text = path.read_text().replace('17.0\t32.0', '18.0\t32.0' if corruption=='capacity' else '17.0\t33.0',1)
        path.write_text(text)
    elif corruption == 'bytes':
        path = directory/'pass_2.segments.txt'; path.write_text(path.read_text()+'\n')
    else:
        path = stage/'openroad-globalrouting.log'; path.write_text(path.read_text().replace('pass=2 nets=', 'pass=3 nets='))
    with pytest.raises(ValueError):
        force.validate_observer(stage, data)


def test_snapshot_numeric_spelling_and_segment_direction_are_semantic(observer):
    stage, data = observer
    directory = stage/'force-observer'
    path = directory/'pass_4.native-grid.tsv'; path.write_text(path.read_text().replace('.0', ''))
    path = directory/'pass_4.boundary-native-grid.tsv'; path.write_text(path.read_text().replace('.0', ''))
    path = directory/'pass_4.segments.txt'
    path.write_text(path.read_text().replace('3600 3600 Metal1 10800 3600 Metal1','10800 3600 Metal1 3600 3600 Metal1'))
    assert force.validate_observer(stage, data)['observer_equivalence_verified']


def test_used_grid_candidate_is_scoped_between_same_process_controls():
    text = force.force_trace(True, rebuild=True)
    call = text.index('log_cmd grt::force_reroute_pair')
    assert text.index(force.EXPECTED_GRID) < text.index('set ::env(WARP_FORCE_REBUILD_USED_GRIDS) 1') < call
    assert call < text.index('unset ::env(WARP_FORCE_REBUILD_USED_GRIDS)')
    assert 'set ::env(WARP_FORCE_REBUILD_USED_GRIDS) 1' not in force.force_trace(True)
    assert 'set ::env(WARP_FORCE_REBUILD_USED_GRIDS) 1' not in force.force_trace(False)
    for repair, rebuild in [(False, True), (True, 1), (True, '1')]:
        with pytest.raises(ValueError):
            force.force_trace(repair, rebuild)


def test_every_case_rejects_inherited_candidate_setting():
    for repair, rebuild in [(False, False), (True, False), (True, True)]:
        text = force.force_trace(repair, rebuild)
        assert text.index('Unexpected inherited used-grid experiment') < text.index('log_cmd global_route')


@pytest.mark.parametrize('name,count,valid', [
    ('default_identity',0,True), ('default_identity',1,False),
    ('forced_pair',0,True), ('forced_pair',1,False),
    ('rebuilt_pair',0,False), ('rebuilt_pair',1,True),
    ('rebuilt_pair',5,True), ('rebuilt_pair',6,False), ('unknown',1,False),
])
def test_native_activation_witness_is_required_only_for_candidate(tmp_path,name,count,valid):
    (tmp_path/'openroad-globalrouting.log').write_text('WARP_FORCE_REBUILD_USED_GRIDS\n'*count)
    if valid:
        assert force.validate_rebuild_witness(tmp_path,name) == count
    else:
        with pytest.raises(ValueError):
            force.validate_rebuild_witness(tmp_path,name)


@pytest.mark.parametrize('failed_control,expected_cases', [
    ('default_identity', ['default_identity']),
    ('legacy_observer', ['default_identity', 'forced_pair']),
    (None, ['default_identity', 'forced_pair', 'rebuilt_pair']),
])
def test_candidate_cannot_run_before_both_controls_pass(tmp_path,monkeypatch,failed_control,expected_cases):
    (tmp_path/'build').mkdir()
    monkeypatch.setattr(force.trace, 'ROOT', tmp_path)
    monkeypatch.setattr(force.trace, 'OUT', tmp_path/'unused')
    monkeypatch.setenv('WARP_FORCE_OPENROAD', '/unused/bin/openroad')
    monkeypatch.setattr(force, 'docker_options', lambda _: ())
    monkeypatch.setattr(force.trace.cfg, 'sha', lambda _: '0'*64)
    monkeypatch.setattr(force.subprocess, 'run', lambda *a, **kw: None)
    called = []
    def replay(*args, **kwargs):
        name = force.trace.OUT.name
        called.append(name)
        stage = force.trace.OUT/'replay'/'1-openroad-globalrouting'
        stage.mkdir(parents=True)
        (stage/'openroad-globalrouting.log').write_text(
            'WARP_FORCE_REBUILD_USED_GRIDS\n' if name == 'rebuilt_pair' else '')
    monkeypatch.setattr(force.trace, 'main', replay)
    def stage_validator(stage, repair):
        if stage.parent.parent.name == failed_control:
            raise ValueError('Injected failed default identity')
        return {}
    def observer_validator(*args):
        if failed_control == 'legacy_observer':
            raise ValueError('Injected failed legacy route identity')
        return {'observer_equivalence_verified': True}
    monkeypatch.setattr(force, 'validate_stage', stage_validator)
    monkeypatch.setattr(force, 'validate_observer', observer_validator)
    monkeypatch.setattr(force, 'validate_rebuilt_control', lambda *args: None)
    monkeypatch.setattr(force, 'qualify_native_corridors', lambda *args: {'controls_qualified': True})
    if failed_control:
        with pytest.raises(ValueError, match='Injected failed'):
            force.main()
    else:
        force.main()
    assert called == expected_cases
    import json
    result = json.loads((tmp_path/'build/route_force_repair/result.json').read_text())
    assert result['diagnostic_completed'] is (failed_control is None)
    assert result['physical_acceptance'] is False

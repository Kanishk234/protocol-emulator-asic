"""Failed-route observer retains native error and rejects malformed exports."""
from pathlib import Path
import shutil
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'test_internal'))
import cloud_route_trace as trace


def test_tool_override_requires_explicit_readonly_pinned_repair_worker():
    args = ['-v', '/nix/store:/nix/store:ro', '-e',
            '_LLN_OVERRIDE_OPENROAD=/nix/store/' + 'a'*32 + '-openroad/bin/openroad']
    trace.validate_execution_options(None, None, ('GRT-0116',), False)
    trace.validate_execution_options('cloud_route_force_repair.py', args, ('GRT-0116', 'GRT-0232'), True)
    for worker, options, errors in (
        ('other.py', args, ('GRT-0116',)),
        ('cloud_route_force_repair.py', ['-v', '/nix/store:/nix/store:rw', *args[2:]], ('GRT-0116',)),
        ('cloud_route_force_repair.py', args, ('ANY',)),
        ('cloud_route_force_repair.py', [*args[:3], '_LLN_OVERRIDE_OPENROAD=/tmp/openroad'], ('GRT-0116',)),
    ):
        with pytest.raises(ValueError):
            trace.validate_execution_options(worker, options, errors, True)


def sample():
    return ''.join(name+'\n(\n10 20 Metal1 10 20 Metal2\n10 20 Metal2 10 40 Metal2\n)\n'
                   for name in sorted(trace.TARGETS))


def test_native_segments_require_all_measured_nets():
    result = trace.parse_segments(sample())
    assert result['native_net_count'] == 4
    assert set(result['targets']) == trace.TARGETS
    with pytest.raises(ValueError, match='absent'):
        trace.parse_segments('n\n(\n0 0 Metal1 10 0 Metal1\n)\n')


@pytest.mark.parametrize('old,new', [('10 40 Metal2','20 40 Metal2'),
    ('10 40 Metal2','10 40 Metal3'), ('Metal1','Metal5'), (')\n','')])
def test_native_segments_reject_unsafe_or_partial_geometry(old,new):
    with pytest.raises(ValueError):trace.parse_segments(sample().replace(old,new))


def test_observer_rethrows_original_native_failure(tmp_path):
    tcl = shutil.which('tclsh')
    if not tcl:pytest.skip('Tcl interpreter unavailable')
    prefix = r'''
set ::env(STEP_DIR) [lindex $argv 0]
proc log_cmd {args} {return -code error -errorcode {GRT 116} "GRT-0116"}
proc write_global_route_segments {path} {set f [open $path w]; puts $f "native witness"; close $f}
set arg_list {-congestion_iterations 50}
proc observer {} {
    global arg_list
'''
    suffix = r'''
}
set status [catch observer message options]
if {$status != 1 || $message ne "GRT-0116" || [dict get $options -errorcode] ne {GRT 116}} {exit 4}
if {![file exists $::env(STEP_DIR)/native-segments.txt]} {exit 5}
'''
    script=tmp_path/'test.tcl';script.write_text(prefix+trace.TRACE+suffix)
    subprocess.run([tcl,str(script),str(tmp_path)],check=True,timeout=5)
    assert (tmp_path/'native-return.txt').read_text() == '1\nGRT-0116\n'


def test_observer_does_not_mask_unrelated_error(tmp_path):
    tcl = shutil.which('tclsh')
    if not tcl:pytest.skip('Tcl interpreter unavailable')
    prefix = r'''
set ::env(STEP_DIR) [lindex $argv 0]
proc log_cmd {args} {error "unrelated"}
proc write_global_route_segments {path} {error "must not export unrelated failure"}
set arg_list {}
proc observer {} {
    global arg_list
'''
    suffix = r'''
}
set status [catch observer message]
if {$status != 1 || $message ne "unrelated"} {exit 4}
'''
    script=tmp_path/'test.tcl';script.write_text(prefix+trace.TRACE+suffix)
    subprocess.run([tcl,str(script),str(tmp_path)],check=True,timeout=5)
    assert not (tmp_path/'native-segments.txt').exists()


def test_persisted_policy_matches_authenticated_original_subset():
    import hashlib
    import json
    digest=hashlib.sha256(json.dumps(trace.ORIGINAL_POLICY,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert digest=='691d8fec64c122e17a8e8016ff38644137275d2e0468925bc3e92d344d016186'
    selected, protected=trace.routing.configure_iterations({},trace.ORIGINAL_POLICY,50)
    assert selected==protected==trace.ORIGINAL_POLICY


def test_regenerated_control_checks_every_historical_view(tmp_path, monkeypatch):
    import cloud_regenerate_control as regen
    expected = {'config.json':'config', 'padded.odb':'odb', 'padded.nl.v':'nl',
                'after.tsv':'census','geometry_after.tsv':'geometry'}
    monkeypatch.setattr(regen.reference,'EXPECTED',expected)
    def fake_sha(path):return path.read_text()
    monkeypatch.setattr(regen.cfg,'sha',fake_sha)
    for name,value in expected.items():(tmp_path/name).write_text(value)
    regen.authenticate_final(tmp_path)
    for name,value in expected.items():
        (tmp_path/name).write_text('changed')
        with pytest.raises(ValueError,match='view differs'):regen.authenticate_final(tmp_path)
        (tmp_path/name).write_text(value)


def test_control_config_does_not_relax_constraints():
    import cloud_regenerate_control as regen
    config={'CLOCK_PERIOD':20,'MAX_FANOUT_CONSTRAINT':10,'CLOCK_UNCERTAINTY_CONSTRAINT':0.25,
            'CLOCK_TRANSITION_CONSTRAINT':0.15,'TIME_DERATING_CONSTRAINT':5,
            'meta':{'version':2,'flow':['old']}}
    actual=regen.final_config(config)
    for key,value in config.items():
        if key!='meta':assert actual[key]==value
    assert actual['CTS_SINK_CLUSTERING_SIZE']==8
    with pytest.raises(ValueError):regen.final_config(dict(config,CLOCK_PERIOD=25))


def test_regeneration_requires_complete_provenance_and_corner_evidence():
    result={'source_run':38167697696,'source_archive_sha256':trace.cfg.SOURCE_SHA,
            'expected_view_sha256':trace.payload.EXPECTED,'sdc_sha256':trace.SDC_SHA}
    with pytest.raises(ValueError,match='corner evidence'):
        trace.authenticate_regeneration(result)
    result['source_archive_sha256']='wrong'
    with pytest.raises(ValueError,match='provenance'):
        trace.authenticate_regeneration(result)


def test_scalar_stage_parser_names_native_scopes_and_rejects_repeats():
    raw = 'After LayerAssignment - 2D/3D cong: 80/145\nAfter MazeRoute3D - 3Dcong: 133\n'
    result = trace.parse_stage_scalars(raw)
    assert result['parsed'] is True
    assert result['after_layer_assignment_2d'] == 80
    assert result['after_layer_assignment_3d'] == 145
    assert result['after_maze_route_3d'] == 133
    with pytest.raises(ValueError, match='Repeated'):
        trace.parse_stage_scalars(raw + raw)
    for incomplete in ('', 'After MazeRoute3D - 3Dcong: nan\n', raw.splitlines()[0]):
        assert trace.parse_stage_scalars(incomplete)['parsed'] is False


def test_scalar_observer_requires_both_exact_final_route_hashes():
    trace.validate_trace_hashes(trace.SEGMENTS_SHA, trace.TARGETS_SHA)
    for segments, targets in (('wrong',trace.TARGETS_SHA), (trace.SEGMENTS_SHA,'wrong')):
        with pytest.raises(ValueError, match='changed authenticated final route'):
            trace.validate_trace_hashes(segments, targets)


def test_d097_budget_comparison_changes_exactly_one_native_field():
    source={'CLOCK_PERIOD':20,'CLOCK_UNCERTAINTY_CONSTRAINT':0.25,
            'MACROS':{'fabric':'unchanged'},'meta':{'version':2}}
    control,protected=trace.selected_policy(source,50)
    candidate,original=trace.selected_policy(source,15)
    assert protected==original==trace.ORIGINAL_POLICY
    assert {key for key in control if control[key]!=candidate[key]}=={'GRT_OVERFLOW_ITERS'}
    assert candidate['GRT_ALLOW_CONGESTION'] is False
    for budget in (0,14,16,100,150):
        with pytest.raises(ValueError,match='budget supported'):
            trace.selected_policy(source,budget)
    with pytest.raises(ValueError,match='disagree'):
        trace.selected_policy(dict(source,GRT_ADJUSTMENT=0.1),15)


def test_grid_replay_uses_only_calibrated_read_only_body():
    import cloud_route_121_grid as grid
    patch=grid.PATCH.read_text()
    modified=grid.observed_trace(trace.TRACE,patch)
    body=patch[patch.index('set warp_grid '):patch.index('close $warp_grid_file')+len('close $warp_grid_file')]+'\n'
    assert modified.replace(body,'',1)==trace.TRACE
    assert modified.count('log_cmd global_route')==1
    assert modified.index(body)<modified.index('if {$warp_route_code != 0}')
    for bad in (patch.replace('close $warp_grid_file',''),patch+patch,
                patch.replace('set warp_grid_file','global_route\nset warp_grid_file')):
        with pytest.raises(ValueError):grid.observed_trace(trace.TRACE,bad)


def test_scalar_debug_instrumentation_only_adds_observation(tmp_path, monkeypatch):
    import json
    original = 'before\n' + trace.reports.COMMAND + '\nafter\n'
    def base(top, common, directory):
        (directory/'common-grt.tcl').write_text(original)
        (directory/'source-sha256.json').write_text('{}')
        (directory/'ATTRIBUTION.md').write_text('Original attribution\n')
        return 'copied top'
    monkeypatch.setattr(trace, 'BASE_INSTRUMENT', base)
    assert trace.instrument(None, None, tmp_path) == 'copied top'
    actual = (tmp_path/'common-grt.tcl').read_text()
    assert actual.count(trace.STAGE_DEBUG) == 1
    assert actual.replace(trace.STAGE_DEBUG+trace.TRACE,trace.reports.COMMAND,1) == original
    assert json.loads((tmp_path/'source-sha256.json').read_text())['trace_common'] == trace.cfg.sha(tmp_path/'common-grt.tcl')


def test_negotiation_trajectory_preserves_ndr_epochs_and_incremented_counter():
    raw = '''[INFO GRT-0102] Start extra iteration 1/50
=== Overflow Iteration 2 - TotalOverflow 180 - OverflowIter 50 - OverflowIncreases 0 - MaxOverIncr 25 ===
[WARNING GRT-0273] Disabled NDR (to reduce congestion) for net: clk
[INFO GRT-0102] Start extra iteration 1/50
=== Overflow Iteration 2 - TotalOverflow 150 - OverflowIter 50 - OverflowIncreases 0 - MaxOverIncr 25 ===
[INFO GRT-0102] Start extra iteration 2/50
=== Overflow Iteration 3 - TotalOverflow 133 - OverflowIter 50 - OverflowIncreases 0 - MaxOverIncr 25 ===
[DEBUG GRT-congestionIterations] Minimal overflow 133 occurring at round 2.
'''
    result = trace.parse_negotiation_epochs(raw)
    assert result['parsed'] is True
    assert result['started_iteration_total'] == 3
    assert result['epochs'][0]['disabled_ndr_after'] == ['clk']
    assert [s['overflow'] for s in result['epochs'][1]['samples']] == [150,133]
    assert result['native_minimum']['round'] == 2
    assert trace.parse_negotiation_epochs(raw.replace('OverflowIter 50','OverflowIter BAD'))['parsed'] is False
    with pytest.raises(ValueError, match='restart without'):
        trace.parse_negotiation_epochs(raw.replace('[WARNING GRT-0273] Disabled NDR (to reduce congestion) for net: clk\n',''))
    with pytest.raises(ValueError, match='post-increment'):
        trace.parse_negotiation_epochs(raw.replace('Overflow Iteration 2','Overflow Iteration 1',1))
    with pytest.raises(ValueError, match='Duplicate'):
        trace.parse_negotiation_epochs(raw + raw.splitlines()[-2]+'\n')


def test_prior_native_log_has_no_invented_iteration_trajectory():
    raw = '[INFO GRT-0102] Start extra iteration 1/50\n'
    result = trace.parse_negotiation_epochs(raw)
    assert result['parsed'] is False
    assert result['observed_epoch_start_counts'] == [1]
    assert trace.parse_negotiation_epochs('')['parsed'] is False

"""Failed-route observer retains native error and rejects malformed exports."""
from pathlib import Path
import shutil
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'test_internal'))
import cloud_route_trace as trace


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

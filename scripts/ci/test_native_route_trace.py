"""Ensure observations preserve the native command sequence and fail closed."""
from pathlib import Path
import shutil
import subprocess

import pytest

from native_route_trace import instrument, STAGES
from native_route_trace_probe import collect


def test_pinned_script_preserves_commands():
    original = Path(__file__).with_name('fixtures').joinpath('native_rsz_timing_postgrt.tcl').read_text()
    patched = instrument(original)
    lines = patched.splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if line.startswith('# Copyright'))
    assert ''.join(line for line in lines[start:]
                   if not line.strip().startswith('tripwire_route_snapshot ')) == original
    assert all(patched.count('tripwire_route_snapshot '+stage+'\n') == 1 for stage in STAGES)


@pytest.mark.parametrize('incremental', [False, True])
def test_tcl_snapshot_execution(tmp_path, incremental):
    tcl = shutil.which('tclsh') or shutil.which('tclsh8.6')
    if not tcl:
        pytest.skip('Tcl interpreter unavailable')
    original = Path(__file__).with_name('fixtures').joinpath('native_rsz_timing_postgrt.tcl').read_text()
    prelude = '''
set ::env(STEP_DIR) [lindex $argv 0]
set ::env(SCRIPTS_DIR) /unused
foreach key {GRT_RESIZER_SETUP_SLACK_MARGIN GRT_RESIZER_SETUP_MAX_BUFFER_PCT GRT_RESIZER_HOLD_SLACK_MARGIN GRT_RESIZER_HOLD_MAX_BUFFER_PCT GRT_RESIZER_FIX_HOLD_FIRST} {set ::env($key) 0}
set ::env(GRT_RESIZER_RUN_GRT) 1
rename source real_source
proc source {path} {puts "NATIVE_SOURCE [file tail $path]"}
proc unknown {args} {return {}}
proc write_db {path} {set f [open $path w]; puts $f database; close $f}
proc write_def {path} {write_db $path}
proc write_verilog {path} {write_db $path}
'''
    script = tmp_path/'instrumented.tcl'
    script.write_text(prelude+instrument(original, incremental=incremental))
    (tmp_path/'after_grt.guide').write_text('guides')
    result = subprocess.run([tcl, str(script), str(tmp_path)], capture_output=True, text=True, check=True)
    assert set(collect(tmp_path, result.stdout)) == set(STAGES)
    observed = [line for line in result.stdout.splitlines()
                if line.startswith('TRIPWIRE_') or line.endswith('grt.tcl') or line.endswith('dpl.tcl')]
    expected = ['NATIVE_SOURCE grt.tcl', 'TRIPWIRE_ROUTE_SNAPSHOT initial_route',
                        'TRIPWIRE_ROUTE_SNAPSHOT timing_repair', 'NATIVE_SOURCE dpl.tcl',
                        'TRIPWIRE_ROUTE_SNAPSHOT placement', 'NATIVE_SOURCE grt.tcl',
                        'TRIPWIRE_ROUTE_SNAPSHOT final_route']
    if incremental:
        expected.pop(-2)
        observed = [line for line in observed if not line.startswith('TRIPWIRE_INCREMENTAL')]
        assert result.stdout.count('TRIPWIRE_INCREMENTAL begin\n') == 1
        assert result.stdout.count('TRIPWIRE_INCREMENTAL end\n') == 1
    assert observed == expected


def test_incremental_tracks_repair_and_placement():
    original = Path(__file__).with_name('fixtures').joinpath('native_rsz_timing_postgrt.tcl').read_text()
    patched = instrument(original, incremental=True)
    assert patched.count('source $::env(SCRIPTS_DIR)/openroad/common/grt.tcl') == 1
    assert patched.index('global_route -start_incremental') < patched.index('# Resize')
    assert patched.index('source $::env(SCRIPTS_DIR)/openroad/common/dpl.tcl') < patched.index('global_route -end_incremental')
    assert patched.index('global_route -end_incremental') < patched.index('tripwire_route_snapshot final_route')


def test_reject_unknown_script():
    with pytest.raises(ValueError, match='Unexpected pinned'):
        instrument('source unreviewed_script.tcl\n')


def test_collect_requires_every_stage_and_view(tmp_path):
    log = ''
    for stage in STAGES:
        root = tmp_path/'route_trace'/stage
        root.mkdir(parents=True)
        for ext in ('odb', 'def', 'v'):
            (root/('snapshot.'+ext)).write_text('evidence '+stage)
        if stage in ('initial_route', 'final_route'):
            (root/'after_grt.guide').write_text('guides '+stage)
        log += 'TRIPWIRE_ROUTE_SNAPSHOT '+stage+'\n'
    assert set(collect(tmp_path, log)) == set(STAGES)
    with pytest.raises(ValueError, match='repeated'):
        collect(tmp_path, log+log)
    (tmp_path/'route_trace'/'placement'/'snapshot.odb').unlink()
    with pytest.raises(ValueError, match='Missing native'):
        collect(tmp_path, log)


def test_no_promotion_and_native_sequence():
    text = Path(__file__).with_name('native_route_trace_probe.py').read_text()
    assert "configure(config)  #" in text
    assert "['OpenROAD.ResizerTimingPostGRT', 'OpenROAD.RepairAntennas']" in text
    assert 'qualified=False, route_authorized=False' in text

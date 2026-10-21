import ast
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
import yaml

import native_route_trace
sys.modules['native_route_trace_base'] = native_route_trace
from wire600_selective_instrument import instrument
from wire600_selective_plan import BINDING, nearest_row, partition, power_anchor, validate_files, validate_proposal
from wire600_selective_screen import timing_config, validate_run

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize('count', [1, 4, 5, 9, 13, 16, 24])
def test_partition_preserves_all_loads_with_headroom(count):
    terms = [('driver', 'Q')] + [(f'sink{i}', 'A') for i in range(count)]
    loc = {n: ('sg13cmos5l_buf_1', i*10, i*5, 'N') for i, (n, p) in enumerate(terms)}
    driver, groups = partition(terms, loc)
    assert driver == ('driver', 'Q')
    assert [p for group in groups for p in group] == terms[1:]
    assert all(1 <= len(g) <= 4 for g in groups)
    assert len(groups) <= 6


@pytest.mark.parametrize('bad', ['CLK', 'GCLK', 'GATE', 'RESET_B'])
def test_protected_loads_rejected(bad):
    with pytest.raises(ValueError, match='Protected'):
        partition([('driver', 'Q'), ('sink', bad)], {'driver': ('sg13cmos5l_dfrbpq_1', 0, 0, 'N')})


def test_excessive_and_ambiguous_loads_rejected():
    with pytest.raises(ValueError):
        partition([('driver', 'Q'), ('other', 'Q')], {})
    with pytest.raises(ValueError):
        partition([('driver', 'Q')] + [('sink'+str(i), 'A') for i in range(25)], {})
    with pytest.raises(ValueError, match='Exposed'):
        partition([('driver', 'Q'), ('PIN', 'pin')], {})


def test_unreviewed_source_and_proposal_rejected(tmp_path):
    for item in BINDING['files'].values():
        p = tmp_path/item['path']
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('unreviewed')
    with pytest.raises(ValueError, match='Wrong selective'):
        validate_files(tmp_path)
    with pytest.raises(ValueError, match='canonical'):
        validate_proposal({'groups': []})


def test_macro_target_row_stays_outside_halo():
    assert nearest_row([(260000, 200000, 'N', 100, 480), (0, 241920, 'FS', 1000, 480)],
                       (50000, 231210)) == [49920, 241920, 'FS']


def test_power_anchor_never_uses_diode_or_macro():
    terms = [('u_chip.u_sram.sram', 'A_DOUT[0]'), ('ANTENNA', 'A'), ('buffer', 'A')]
    loc = {'u_chip.u_sram.sram': ('RM_IHPSG13_1P_512x16_c2_bm_bist', 0, 0, 'FS'),
           'ANTENNA': ('sg13cmos5l_antennanp', 0, 0, 'N'),
           'buffer': ('sg13cmos5l_buf_4', 0, 0, 'N')}
    assert power_anchor(terms, loc, terms[0]) == 'buffer'
    with pytest.raises(ValueError, match='power anchor'):
        power_anchor(terms[:2], loc, terms[0])


def test_source_provenance_is_exact():
    run = dict(id=BINDING['source_run'], head_sha=BINDING['source_head'], head_branch='main',
               path=BINDING['source_path'], conclusion='failure')
    validate_run(run)
    for key in run:
        bad = dict(run, **{key: 'wrong'})
        with pytest.raises(ValueError):
            validate_run(bad)


def test_timing_configs_preserve_relative_macro_base(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path/'src').mkdir()
    macro = tmp_path/'macro/sram.gds'
    macro.parent.mkdir()
    macro.write_text('geometry')
    config = {'MACROS': {'sram': {'gds': ['dir::../macro/sram.gds']}}, 'CLOCK_PERIOD': 20}
    path = timing_config(config)
    assert path.parent == Path(BINDING['files']['config']['path']).parent
    assert path.parent == Path('src')
    import json
    assert json.loads(path.read_text()) == config
    relative = config['MACROS']['sram']['gds'][0].removeprefix('dir::')
    for sibling in (path, path.with_name('config_timing_after-fast.json')):
        assert (sibling.parent/relative).resolve() == macro.resolve()
        assert (sibling.parent/relative).is_file()


def test_instrument_preserves_native_timing_after_audited_edits():
    original = (ROOT/'scripts/ci/fixtures/native_rsz_timing_postgrt.tcl').read_text()
    result = instrument(original)
    assert result.index('global_route -start_incremental') < result.index('selective.before.v')
    assert result.index('selective.after.v') < result.index('repair_timing')
    assert result.index('tripwire_restore_placement_status') < result.index('selective.after.v')
    assert result.count('global_route -end_incremental') == 2
    assert result.count('global_route -start_incremental') == 2
    assert result.count('estimate_parasitics -global_routing') == 1
    assert (result.index('selective.after.v') < result.index('global_route -end_incremental')
            < result.index('estimate_parasitics -global_routing')
            < result.index('TRIPWIRE_INCREMENTAL begin') < result.index('repair_timing'))
    with pytest.raises(ValueError, match='pinned'):
        instrument(original+'# unknown change\n')


def test_image_module_layout_imports_and_instruments(tmp_path):
    shutil.copyfile(ROOT/'scripts/ci/native_route_trace.py', tmp_path/'native_route_trace_base.py')
    shutil.copyfile(ROOT/'scripts/ci/wire600_selective_instrument.py', tmp_path/'native_route_trace.py')
    code = '''import runpy, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
m = runpy.run_path(str(Path(sys.argv[1])/'native_route_trace.py'))
assert 'selective.before.v' in m['instrument'](Path(sys.argv[2]).read_text())
'''
    subprocess.run([sys.executable, '-c', code, str(tmp_path),
                    str(ROOT/'scripts/ci/fixtures/native_rsz_timing_postgrt.tcl')], check=True)


def test_instrument_executes_with_tcl(tmp_path):
    tcl = shutil.which('tclsh') or shutil.which('tclsh8.6')
    if not tcl:
        pytest.skip('Tcl interpreter unavailable')
    original = (ROOT/'scripts/ci/fixtures/native_rsz_timing_postgrt.tcl').read_text()
    prelude = '''set ::env(STEP_DIR) [lindex $argv 0]
set ::env(SCRIPTS_DIR) /unused
foreach key {GRT_RESIZER_SETUP_SLACK_MARGIN GRT_RESIZER_SETUP_MAX_BUFFER_PCT GRT_RESIZER_HOLD_SLACK_MARGIN GRT_RESIZER_HOLD_MAX_BUFFER_PCT GRT_RESIZER_FIX_HOLD_FIRST} {set ::env($key) 0}
set ::env(GRT_RESIZER_RUN_GRT) 1
rename source real_source
proc source {path} {puts "SOURCE [file tail $path]"}
proc unknown {args} {return {}}
set parasitics_ready 0
set invalid_parasitics 0
rename source observed_source
proc source {path} {
    if {[file tail $path] eq "wire600_selective_targets.tcl" && $::parasitics_ready} {
        set ::invalid_parasitics 1
    }
    observed_source $path
}
proc estimate_parasitics {args} {set ::parasitics_ready 1}
proc repair_timing {args} {
    if {[lsearch -exact $args -hold]>=0 && $::invalid_parasitics} {
        error "EST-0104: edits after estimator initialization"
    }
}
proc log_cmd {command args} {
    if {$command eq "repair_timing"} {repair_timing {*}$args}
}
proc write_db {path} {set f [open $path w]; puts $f database; close $f}
proc write_def {path} {write_db $path}
proc write_verilog {path} {write_db $path}
'''
    script = tmp_path/'instrumented.tcl'
    script.write_text(prelude+instrument(original))
    (tmp_path/'after_grt.guide').write_text('guides')
    result = subprocess.run([tcl, str(script), str(tmp_path)], capture_output=True, text=True, check=True)
    assert result.stdout.count('SOURCE wire600_selective_targets.tcl') == 1
    assert result.stdout.count('TRIPWIRE_SELECTIVE repaired and refreshed') == 1
    assert all((tmp_path/f'selective.{stage}.v').is_file() for stage in ('before', 'after'))
    # Model the estimator guard's dirty-cache precondition. Reintroducing an
    # estimate before direct ODB edits must reject even if estimated again.
    bad = instrument(original).replace('write_verilog $::env(STEP_DIR)/selective.before.v',
        'estimate_parasitics -global_routing\nwrite_verilog $::env(STEP_DIR)/selective.before.v', 1)
    script.write_text(prelude+bad)
    negative_root = tmp_path/'negative'
    negative_root.mkdir()
    (negative_root/'after_grt.guide').write_text('guides')
    negative = subprocess.run([tcl, str(script), str(negative_root)], capture_output=True, text=True)
    assert negative.returncode != 0
    assert 'EST-0104: edits after estimator initialization' in negative.stderr


def test_checkpoint_workflow_has_no_detailed_route_and_parses():
    job = yaml.safe_load((ROOT/'.github/workflows/gds-wire600-selective-screen.yaml').read_text())['jobs']['harden']
    steps = job['steps']
    download = next(s['with'] for s in steps if s['name'] == 'Download exact failed wire600 checkpoint')
    assert download['run-id'] == BINDING['source_run']
    text = '\n'.join(s.get('run', '') for s in steps)
    assert 'wire600_selective_screen.py' in text
    for s in steps:
        if 'run' not in s:
            continue
        subprocess.run(['bash', '-n'], input=s['run'], text=True, check=True)
        if "<<'PY'\n" in s['run']:
            ast.parse(s['run'].split("<<'PY'\n", 1)[1].split('\nPY', 1)[0])

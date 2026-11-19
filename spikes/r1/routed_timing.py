"""Configured macro RC timing diagnostic; never full-chip timing acceptance.

Use the source-proven explicit-alias view, the real loaded configuration and
the geometry-identical full-macro SPEF. Retain ideal/cell-only controls and
reject missing annotation on active timing and clock cones.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

from assembly_catalog import sha
from flat_reference import normalize_cells
from flat_topology import verify
from run_timing import LIB_SHA, compare, parse_log, quoted

SPEF_SHA = 'e3ba5b5b8f1c1db15633fa1df1aa792756ffade6f586fec68945d504bd2112a3'
ANALYSIS_SHA = '3db2dbd2bf5c9ef100925b97c99065cd6a4de2f0e6add954714639f38da3d9dc'
SNAPSHOT_SHA = '5f9aa3bfb07e21b5238b0da1472980ba927842bc732b8e7cdde29923d6e06227'
IMAGE_SHA = '25bfec380cbd5fb8cac4390389d1c1fa14d33ddb946e6499fc7467f79ee100b2'
SCOPE = ('Configured primary-image macro setup/hold diagnostic at 20ns, propagated clocks, '
         '0.25ns uncertainty, nominal extracted RC and slow/fast cells. Macro I/O '
         'delays remain the original conditional zero-delay boundary. No shell, '
         'loading-mode, physical power/LVS, complete-corner or submission acceptance.')


def observed_cases(snapshot):
    tiles = snapshot['tiles']
    if len(tiles) != 40:
        raise ValueError('Incomplete observed tile configuration')
    values = {}
    for tile, row in tiles.items():
        for cell, value in row['q'].items():
            name = tile + '/' + cell + '/Q'
            if value not in ('0', '1') or name in values:
                raise ValueError('Invalid observed configuration')
            values[name] = value
    if len(values) != 8736:
        raise ValueError('Incomplete observed latch configuration')
    return values


def assert_cases(text, values):
    pairs = re.findall(r'set p \[get_pins -quiet \{([^{}]+/Q)\}\]\n'
                       r'if \{\[llength \$p\]!=1\} \{error "missing configuration pin"\}\n'
                       r'set_case_analysis ([01]) \$p\nincr observed', text)
    if len(pairs) != len(values) or len(dict(pairs)) != len(pairs) or dict(pairs) != values:
        raise ValueError('Timing cases differ from real loaded configuration')
    if re.search(r'\bset_(?:false_path|multicycle_path|disable_timing)\b', text):
        raise ValueError('Unexpected timing exception')


ANNOTATION = '''
puts "R1_ANNOTATION_BEGIN"
report_parasitic_annotation -report_unannotated
puts "R1_ANNOTATION_END"
set active_targets {}
foreach p $paths {lappend active_targets [get_property $p endpoint]}
set active_targets [concat $active_targets [all_registers -edge_triggered -clock run -clock_pins]]
if {[llength $active_targets]==0} {error "no active timing targets"}
set active_names [dict create]
foreach p [get_fanin -to $active_targets -flat -trace_arcs timing] {dict set active_names [get_full_name $p] 1}
foreach name [lsort [dict keys $active_names]] {puts "R1_ACTIVE_PIN\\t$name"}
puts "R1_ACTIVE_END"
'''


def render(template, values, liberty, analysis, spef, mode, hold=False):
    """Retain original observed-state, frame, reset and FF coverage guards."""
    # The compiler/FASM dependency is only needed in the preparation venv.
    # The pinned STA image consumes the prepared scripts without that package.
    from unused_lut_probe import change_case
    if template.count('link_design eFPGA\n') != 1 or mode not in ('control', 'routed'):
        raise ValueError('Unexpected timing template or mode')
    body = template.split('link_design eFPGA\n', 1)[1]
    body = change_case(body, dict(tile='Tile_X2Y3_LUT4x8_ha', cell='_1560_'))
    assert_cases(body, values)
    clock = 'create_clock -name run -period 20 [get_ports Tile_X1Y4_A_OUT_top]'
    if body.count(clock) != 1 or body.count('puts "RUNSTA_END"') != 1:
        raise ValueError('Unexpected clock or completion marker')
    if mode == 'routed':
        body = body.replace(clock, clock + '\nset_propagated_clock [all_clocks]\nset_clock_uncertainty 0.25 [all_clocks]')
    delay = 'min' if hold else 'max'
    body = body.replace('-path_delay max', '-path_delay ' + delay)
    body = body.replace('report_checks -path_delay', 'report_checks -format full_clock_expanded -path_delay')
    suffix = ANNOTATION
    if mode == 'routed':
        suffix += 'report_clock_skew -' + ('hold' if hold else 'setup') + ' -digits 6\n'
    body = body.replace('puts "RUNSTA_END"', suffix + 'puts "RUNSTA_END"')
    header = template.splitlines()[0] + '\nread_liberty ' + quoted(liberty)
    header += '\nread_verilog ' + quoted(analysis) + '\nlink_design warp_r1_candidate\n'
    if mode == 'routed':
        header += 'read_spef ' + quoted(spef) + '\n'
    return header + body


def annotation(text):
    begin, end = 'R1_ANNOTATION_BEGIN\n', 'R1_ANNOTATION_END\n'
    if text.count(begin) != 1 or text.count(end) != 1 or text.count('R1_ACTIVE_END\n') != 1:
        raise ValueError('Incomplete annotation evidence')
    block = text.split(begin)[1].split(end)[0]
    rows = block.splitlines()
    missing = []
    for kind in ('unannotated', 'partially unannotated'):
        if not rows:
            raise ValueError('Missing annotation census')
        match = re.fullmatch(r'Found (\d+) ' + kind + r' drivers\.', rows.pop(0))
        if not match:
            raise ValueError('Unknown annotation report format')
        count = int(match[1]); names = rows[:count]; rows = rows[count:]
        if len(names) != count or any(not n.startswith(' ') or not n.strip() for n in names):
            raise ValueError('Truncated annotation report')
        missing.extend(n.strip() for n in names)
    if rows or len(missing) != len(set(missing)):
        raise ValueError('Unexpected or duplicate missing driver evidence')
    active = re.findall(r'^R1_ACTIVE_PIN\t(.+)$', text, re.M)
    if not active or len(active) != len(set(active)):
        raise ValueError('Empty or duplicate active timing cone')
    uncovered = sorted(set(active) & set(missing))
    return dict(active_pins=len(active), all_missing_drivers=len(missing),
                active_missing_drivers=uncovered, passed=not uncovered)


def prepare(rc, proof, native, capsule, pdk, out):
    rc, proof, native, capsule, pdk, out = (Path(p).resolve() for p in (rc, proof, native, capsule, pdk, out))
    result = json.loads((rc/'result.json').read_text())
    xor = result['geometry_xor']
    if (not result['passed'] or not xor['passed'] or xor['layers_compared'] != 21
            or xor['layers_with_differences'] != 0 or xor['ignored_geometry_layers']
            or not xor['negative_control_detected']):
        raise ValueError('Require complete source geometry equivalence before RC timing')
    spef = rc/'extract/1-openroad-rcx/nom/warp_r1_candidate.nom.spef'
    if sha(spef) != SPEF_SHA or spef.stat().st_size != 35585561:
        raise ValueError('Extracted full-macro SPEF differs')
    if sum(line.startswith('*D_NET ') for line in spef.open()) != 26765:
        raise ValueError('Extracted net census differs')
    analysis = proof/'analysis.v'; source_proof = json.loads((proof/'proof.json').read_text())
    if not source_proof['passed'] or sha(analysis) != ANALYSIS_SHA or source_proof['analysis_sha256'] != ANALYSIS_SHA:
        raise ValueError('Require source-proven explicit-alias timing view')
    inventory_path = rc/'expected.json'; inventory = json.loads(inventory_path.read_text())
    if sha(inventory_path) != 'a740e6ff2ea35e4ff52bb3881f2165cf418f64e9c28d569a445c43978417ea03':
        raise ValueError('Physical source signal inventory changed')
    top_path = capsule/'analysis/top.json'
    top = json.loads(top_path.read_text())['modules']['eFPGA']
    proofs = {}
    for name in ('source', 'analysis'):
        module = json.loads((proof/(name+'.json')).read_text())['modules']['warp_r1_candidate']
        if name == 'source':
            module = normalize_cells(module, list(top['cells']))
        proofs[name] = verify(inventory, top['ports'], module)
        if not proofs[name]['passed'] or proofs[name]['cells'] != 45429:
            raise ValueError('Complete source connectivity proof failed')
    functional = native/'registered_functional/candidate'
    functional_proof = json.loads((functional/'configured-smoke.json').read_text())
    snapshot = functional/'configuration-state.json'; image = functional/'registered-input.wbit'
    if (not functional_proof['passed'] or not functional_proof['user_restart_probe_tested']
            or sha(snapshot) != SNAPSHOT_SHA or functional_proof['configuration_snapshot']['sha256'] != SNAPSHOT_SHA
            or sha(image) != IMAGE_SHA or functional_proof['postphysical_tile_instances_tested'] != 40):
        raise ValueError('Require the actual passing native candidate configuration')
    shell = native/'registered_functional/shell/configuration-state.json'
    if sha(shell) != SNAPSHOT_SHA:
        raise ValueError('Direct and management-loaded configuration differ')
    values = observed_cases(json.loads(snapshot.read_text()))
    libdir = pdk/'ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib'
    slow = libdir/'sg13cmos5l_stdcell_slow_1p08V_125C.lib'
    fast = libdir/'sg13cmos5l_stdcell_fast_1p32V_m40C.lib'
    if sha(slow) != LIB_SHA or not fast.is_file():
        raise ValueError('Pinned PDK cell libraries missing or changed')
    out.mkdir(parents=True, exist_ok=False)
    cases = {}
    for name, mode, hold, liberty in [('cell_control', 'control', False, slow),
                                     ('routed_setup', 'routed', False, slow),
                                     ('routed_hold', 'routed', True, fast)]:
        for policy in ('static', 'dynamic'):
            template = capsule/'analysis'/(policy+'.tcl')
            target = out/(name+'_'+policy+'.tcl')
            target.write_text(render(template.read_text(), values, liberty, analysis, spef, mode, hold))
            cases[target.stem] = sha(target)
    paths = [Path(__file__), Path(__file__).with_name('run_timing.py'), Path(__file__).with_name('unused_lut_probe.py'),
             rc/'result.json', inventory_path, spef, proof/'proof.json', analysis, proof/'source.json', proof/'analysis.json',
             snapshot, image, shell, functional/'configured-smoke.json', slow, fast, top_path,
             capsule/'analysis/static.tcl', capsule/'analysis/dynamic.tcl']
    plan = dict(input_sha256={str(p): sha(p) for p in paths}, rendered_sha256=cases,
                source_proofs=proofs, observed_configuration=8736, candidate_image_sha256=IMAGE_SHA,
                spef_sha256=SPEF_SHA, scope=SCOPE)
    (out/'plan.json').write_text(json.dumps(plan, indent=2)+'\n')


def run(out):
    out = Path(out).resolve(); plan = json.loads((out/'plan.json').read_text())
    result = dict(passed=False, diagnostic_complete=False, physical_acceptance=False,
                  timing_acceptance=False, scope=SCOPE, run=os.environ.get('GITHUB_RUN_ID'),
                  source_sha=os.environ.get('GITHUB_SHA'), cases={})
    try:
        for path, digest in plan['input_sha256'].items():
            if sha(path) != digest:
                raise ValueError('Frozen timing input changed')
        for name, digest in plan['rendered_sha256'].items():
            script = out/(name+'.tcl')
            if sha(script) != digest:
                raise ValueError('Timing script changed')
            with (out/(name+'.log')).open('w') as stream:
                proc = subprocess.run(['sta', '-exit', str(script)], stdout=stream, stderr=subprocess.STDOUT, timeout=240)
            result['cases'][name] = dict(returncode=proc.returncode)
        models = {}
        annotations = {}
        for name in ('cell_control', 'routed_setup', 'routed_hold'):
            logs = [(out/(name+'_'+p+'.log')).read_text() for p in ('static', 'dynamic')]
            models[name] = compare(*(parse_log(log) for log in logs))
            for policy, log in zip(('static', 'dynamic'), logs):
                key = name+'_'+policy
                annotations[key] = annotation(log)
                if result['cases'][key]['returncode'] != 0:
                    raise ValueError('OpenSTA execution failed: '+key)
                if name != 'cell_control' and 'clock network delay (propagated)' not in log:
                    raise ValueError('Missing propagated-clock path evidence: '+key)
        result.update(models=models, annotation=annotations, diagnostic_complete=True)
        if any(annotations['cell_control_'+p]['passed'] for p in ('static', 'dynamic')):
            raise ValueError('Missing-SPEF negative control was not detected')
        if any(not a['passed'] for k, a in annotations.items() if not k.startswith('cell_control_')):
            raise ValueError('Active clock/data parasitics are incomplete')
        if models['cell_control']['loop_policy_sensitive'] or abs(models['cell_control']['worst_slack_ns']-1.508933)>1e-5:
            raise ValueError('Flat cell-only view does not reproduce the passing primary control')
        result['configured_macro_model_passed'] = all(not models[n]['loop_policy_sensitive'] and
            models[n]['worst_slack_ns'] >= 0 for n in ('routed_setup', 'routed_hold'))
        result['passed'] = result['configured_macro_model_passed']
        if not result['passed']:
            raise ValueError('Configured macro setup/hold or loop-policy check fails')
    except Exception as exc:
        result['error'] = str(exc)
    (out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    if not result['passed']:
        raise SystemExit(result['error'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    p = sub.add_parser('prepare')
    for name in ('rc', 'proof', 'native', 'capsule', 'pdk', 'out'):
        p.add_argument('--'+name, type=Path, required=True)
    sub.add_parser('run').add_argument('--out', type=Path, required=True)
    args = vars(parser.parse_args()); mode = args.pop('mode')
    (prepare if mode == 'prepare' else run)(**args)

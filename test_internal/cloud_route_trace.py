"""Exact best133 replay with failed-route segment export; no acceptance waiver."""
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import cloud_cfg_fanout as cfg
import cloud_hold_allocation as payload
import cloud_congestion_map as reports
import cloud_fanout_grt as routing
from cloud_hotspot_grt import validate_native_policy

ROOT = cfg.ROOT
SOURCE = ROOT / 'build/route_trace_input/baseline'
OUT = ROOT / 'build/route_trace'
TARGETS = {'cell_val[30]', 'cell_pad[27]', 'cell_pad[31]', 'cell_val[27]'}
BASE_INSTRUMENT = reports.instrument
REPORT_SHA = '8e2f5c5003e495d3d347be7d593bb4bbc7801723db2902c3cb530e70a157a1df'
SDC_SHA = '2fd4e213532d83ee258899b6fc1ed48c4e5d91ddb0ccbe21eea0226cc90fd56e'
SEGMENTS_SHA = 'aee9b65f2cfc5f653793de924dedd919a7b68d67fa3ef3febf7ca17e3f1ad7ca'
TARGETS_SHA = 'f00a6206d105a949428454017fe32fa6553bf07c89428c95ac1d7ead661e37d4'
STAGE_DEBUG = ('log_cmd set_debug_level GRT grtSteps 1\n'
               'log_cmd set_debug_level GRT congestionIterations 1\n')
# Exact RT_/GRT_ subset of authenticated38101639866 config660afb662cbb5307… .
ORIGINAL_POLICY = {'RT_MIN_LAYER': 'Metal1', 'RT_MAX_LAYER': 'Metal4', 'RT_CLOCK_MIN_LAYER': None, 'RT_CLOCK_MAX_LAYER': None, 'GRT_ADJUSTMENT': 0.3, 'GRT_MACRO_EXTENSION': 0, 'GRT_LAYER_ADJUSTMENTS': [0, 0, 0, 0, 0], 'GRT_ALLOW_CONGESTION': False, 'GRT_ANTENNA_REPAIR_ITERS': 3, 'GRT_OVERFLOW_ITERS': 50, 'GRT_ANTENNA_REPAIR_MARGIN': 10, 'GRT_ANTENNA_REPAIR_JUMPER_ONLY': False, 'GRT_ANTENNA_REPAIR_DIODE_ONLY': False}
TRACE = r'''
set warp_route_code [catch {log_cmd global_route {*}$arg_list} warp_route_error warp_route_options]
set warp_observer [open $::env(STEP_DIR)/native-return.txt w]
puts $warp_observer $warp_route_code
puts $warp_observer $warp_route_error
close $warp_observer
# Export only the actual native state. Never enable congestion acceptance.
if {$warp_route_code == 0 || [string match {*GRT-0116*} $warp_route_error]} {
    write_global_route_segments $::env(STEP_DIR)/native-segments.txt
}
if {$warp_route_code != 0} {return -options $warp_route_options $warp_route_error}
'''


def instrument(top, common, directory):
    # Original pinned/licensed source copying and report flags are inherited.
    result = BASE_INSTRUMENT(top, common, directory)
    copied = directory / 'common-grt.tcl'
    original = copied.read_text()
    if original.count(reports.COMMAND) != 1:
        raise ValueError('Nonunique native route call')
    observation = STAGE_DEBUG + TRACE
    modified = original.replace(reports.COMMAND, observation)
    if modified.replace(observation, reports.COMMAND, 1) != original:
        raise ValueError('Unexpected observer mutation')
    copied.write_text(modified)
    hashes = json.loads((directory / 'source-sha256.json').read_text())
    hashes['trace_common'] = cfg.sha(copied)
    (directory / 'source-sha256.json').write_text(json.dumps(hashes, indent=2)+'\n')
    with (directory / 'ATTRIBUTION.md').open('a') as f:
        f.write('Observer enables existing GRT/grtSteps and congestionIterations level1 reporting, exports raw segments after native routing, then rethrows its original failure.\n')
    return result


def parse_segments(text):
    """Validate native DBU segment grammar before selecting the measured nets."""
    lines = text.splitlines()
    nets = {}
    index = 0
    while index < len(lines):
        name = lines[index].replace('\\', '')
        if not name or name in nets or index+1 >= len(lines) or lines[index+1] != '(':
            raise ValueError('Malformed/duplicate native net header')
        index += 2
        segments = []
        while index < len(lines) and lines[index] != ')':
            f = lines[index].split()
            if len(f) != 6 or f[2] not in ('Metal1','Metal2','Metal3','Metal4') or f[5] not in ('Metal1','Metal2','Metal3','Metal4'):
                raise ValueError('Malformed native segment/layer')
            x0,y0,x1,y1 = map(int,(f[0],f[1],f[3],f[4]))
            if (x0 != x1 and y0 != y1) or (f[2] != f[5] and (x0 != x1 or y0 != y1)):
                raise ValueError('Non-Manhattan native segment')
            segments.append([x0,y0,f[2],x1,y1,f[5]])
            index += 1
        if index >= len(lines) or not segments:
            raise ValueError('Incomplete/empty native net')
        nets[name] = segments
        index += 1
    if not TARGETS <= set(nets):
        raise ValueError('Measured suspect nets absent in route export')
    return {'native_net_count':len(nets), 'coordinate_unit':'database units; native source DBU1000',
            'targets':{name:nets[name] for name in sorted(TARGETS)}}


def parse_stage_scalars(raw):
    """Only two exact pinned FastRoute logger grammars; no tree inference."""
    patterns = {
        'after_layer_assignment': r'^After LayerAssignment - 2D/3D cong: (\d+)/(\d+)$',
        'after_maze_route_3d': r'^After MazeRoute3D - 3Dcong: (\d+)$',
    }
    found = {name: re.findall(pattern, raw, re.MULTILINE) for name, pattern in patterns.items()}
    if any(len(values) > 1 for values in found.values()):
        raise ValueError('Repeated scalar routing stages')
    if not all(found.values()):
        return {'parsed': False, 'reason': 'Exact pinned stage lines incomplete; retain native log without scalar claim'}
    planar, assigned = map(int, found['after_layer_assignment'][0])
    return {'parsed': True, 'after_layer_assignment_2d': planar,
            'after_layer_assignment_3d': assigned,
            'after_maze_route_3d': int(found['after_maze_route_3d'][0]),
            'scope': 'Native scalar stage observations only; no selected-net topology'}


def validate_trace_hashes(segments_sha, targets_sha):
    if segments_sha != SEGMENTS_SHA or targets_sha != TARGETS_SHA:
        raise ValueError('Scalar observer changed authenticated final route segments')


def parse_negotiation_epochs(raw):
    """Keep source loop counters and NDR resets distinct from command budget."""
    epochs = []
    minimum = None
    missing = False
    for line in raw.splitlines():
        start = re.search(r'\[INFO GRT-0102\] Start extra iteration (\d+)/(\d+)$', line)
        if start:
            iteration, budget = map(int, start.groups())
            if iteration == 1:
                if epochs and not epochs[-1]['disabled_ndr_after']:
                    raise ValueError('Negotiation restart without native NDR-reset witness')
                epochs.append({'budget': budget, 'started_iterations': [],
                               'samples': [], 'disabled_ndr_after': []})
            if not epochs or budget != epochs[-1]['budget']:
                raise ValueError('Negotiation budget/epoch mismatch')
            expected = len(epochs[-1]['started_iterations']) + 1
            if iteration != expected or iteration > budget:
                raise ValueError('Nonsequential native negotiation iterations')
            epochs[-1]['started_iterations'].append(iteration)
        sample = re.search(r'=== Overflow Iteration (\d+) - TotalOverflow (\d+) - OverflowIter (\d+) - OverflowIncreases (-?\d+) - MaxOverIncr (\d+) ===$', line)
        if sample:
            counter, overflow, budget, increases, maximum = map(int, sample.groups())
            if not epochs or not epochs[-1]['started_iterations']:
                raise ValueError('Negotiation sample without iteration')
            epoch = epochs[-1]
            if counter != epoch['started_iterations'][-1]+1 or budget != epoch['budget']:
                raise ValueError('Negotiation post-increment counter mismatch')
            if len(epoch['samples']) >= len(epoch['started_iterations']):
                raise ValueError('Duplicate negotiation sample')
            epoch['samples'].append({'post_increment_counter': counter,
                'overflow': overflow, 'overflow_increases': increases,
                'maximum_overflow_increases': maximum})
        disabled = re.search(r'\[WARNING GRT-0273\] Disabled NDR \(to reduce congestion\) for net: (.+)$', line)
        if disabled:
            if not epochs:
                raise ValueError('NDR reset before negotiation epoch')
            epochs[-1]['disabled_ndr_after'].append(disabled[1])
        best = re.search(r'Minimal overflow (\d+) occurring at round (\d+)\.$', line)
        if best:
            if minimum is not None:
                raise ValueError('Repeated native minimal-overflow report')
            minimum = {'overflow': int(best[1]), 'round': int(best[2]),
                       'scope': 'Native cached minimum/round; not a saved tree checkpoint'}
    if not epochs:
        return {'parsed': False, 'reason': 'No native negotiation epochs; raw log retained'}
    for epoch in epochs:
        if len(epoch['samples']) != len(epoch['started_iterations']):
            missing = True
    if missing:
        return {'parsed': False, 'reason': 'Incomplete exact native iteration samples; raw log retained',
                'observed_epoch_start_counts': [len(e['started_iterations']) for e in epochs]}
    return {'parsed': True, 'epochs': epochs, 'native_minimum': minimum,
            'started_iteration_total': sum(len(e['started_iterations']) for e in epochs),
            'scope': 'Native per-epoch scalar trajectory, post-increment counters; no intermediate net trees'}


def authenticate():
    for name,digest in payload.EXPECTED.items():
        if cfg.sha(SOURCE/name) != digest: raise ValueError('Best133 source differs: '+name)
    result=json.loads((SOURCE/'result.json').read_text())
    if result.get('regenerated') is True:
        authenticate_regeneration(result)
    elif cfg.sha(SOURCE/'result.json') != '28739ad6b5379ef6ed299d1b5c613b577c8059be9807a3e407c179dca74a48cb':
        raise ValueError('Producer result differs')


def authenticate_regeneration(result):
    if (result.get('source_run')!=38167697696 or result.get('source_archive_sha256')!=cfg.SOURCE_SHA
            or result.get('expected_view_sha256')!=payload.EXPECTED or result.get('sdc_sha256')!=SDC_SHA):
        raise ValueError('Regenerated provenance differs')
    corners={'nom_fast_1p32V_m40C','nom_typ_1p20V_25C','nom_slow_1p08V_125C'}
    if set(result.get('corners',{}))!=corners:raise ValueError('Incomplete regenerated corner evidence')
    for corner,case in result['corners'].items():
        if (case['odb_sha256']!=payload.EXPECTED['padded.odb'] or
                case['nl_sha256']!=payload.EXPECTED['padded.nl.v'] or case['sdc_sha256']!=SDC_SHA):
            raise ValueError('Regenerated timing views differ')
        m=case['metrics']
        for kind,minimum in (('setup',0),('hold',0.1)):
            value=m[f'timing__{kind}__ws__corner:{corner}']
            if not isinstance(value,(int,float)) or not math.isfinite(value) or value<minimum or (kind=='setup' and value==0):
                raise ValueError('Regenerated timing guard lost')
            if m[f'timing__{kind}_vio__count__corner:{corner}']!=0:raise ValueError('Regenerated timing violation')
        if any(m[f'design__{kind}_violation__count__corner:{corner}']!=0
                for kind in ('max_fanout','max_slew','max_cap')):
            raise ValueError('Regenerated electrical violation')



def selected_policy(config, iterations):
    if iterations not in (15, 50):
        raise ValueError('Only authenticated50 or D097 early-stop15 budget supported')
    baseline, protected = routing.configure_iterations(config, dict(ORIGINAL_POLICY), 50)
    selected = dict(baseline, GRT_OVERFLOW_ITERS=iterations)
    if {key for key in baseline if baseline[key] != selected[key]} != (
            {'GRT_OVERFLOW_ITERS'} if iterations == 15 else set()):
        raise ValueError('Early-stop changes more than the iteration budget')
    return selected, protected


def main(iterations=50, worker=None, reduced_nets=None):
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise ValueError('Native replay only on hosted runner')
    if iterations not in (15, 50):
        raise ValueError('Unapproved native iteration budget')
    if reduced_nets is not None and (iterations != 15 or not reduced_nets or
            not set(reduced_nets) <= {'cell_pad[31]', 'cell_val[30]'} or
            len(set(reduced_nets)) != len(reduced_nets)):
        raise ValueError('Unapproved diagnostic net reduction')
    OUT.mkdir(exist_ok=False)
    result={'diagnostic_completed':False,'physical_acceptance':False,'route_passed':False,
            'source_run':38167697696,'reference_route_run':38453870785,
            'iteration_budget':iterations,'experimental_budget':iterations!=50}
    try:
        authenticate()
        archive=ROOT/'build/fanout-preflight-source.tar.gz'
        if cfg.sha(archive)!=cfg.SOURCE_SHA:raise ValueError('Archive differs')
        bundle=payload.prepare_payload(archive,SOURCE/'original_source')
        config=cfg.transform(json.loads((bundle/'config.json').read_text()),
            lambda s:s.replace('@BUNDLE@',str(bundle)).replace('@PDK@',os.environ['PDK_ROOT']))
        if config.get('PAD_LIBS') is None:config['PAD_LIBS']={}
        config['CTS_SINK_CLUSTERING_SIZE']=8
        config['meta']={'version':2,'flow':['OpenROAD.GlobalRouting']}
        original=dict(ORIGINAL_POLICY)
        config,protected=selected_policy(config,iterations)
        result['protected_routing_settings']=protected
        result['selected_routing_settings']={key:config[key] for key in protected}
        path=OUT/'config.json';path.write_text(json.dumps(config))
        sdc=SOURCE/'padded_sta_nom_typ_1p20V_25C/final/sdc/tt_um_warp.sdc'
        if cfg.sha(sdc)!=SDC_SHA:raise ValueError('Source SDC differs')
        state=OUT/'state.json';state.write_text(json.dumps({'odb':str(SOURCE/'padded.odb'),
            'nl':str(SOURCE/'padded.nl.v'),'sdc':str(sdc),'metrics':{}}))
        run=OUT/'replay';run.mkdir()
        cmd=['docker','run','--rm','-v',f'{ROOT}:{ROOT}','-w',str(ROOT),'-e',
            f"PDK_ROOT={os.environ['PDK_ROOT']}",'--entrypoint','python3',cfg.IMAGE,
            str(Path(worker or __file__).resolve()),'--inside',str(path),str(state),str(run)]
        with (OUT/'replay.log').open('w') as log:
            process=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=900)
        stage,=run.glob('*-openroad-globalrouting')
        raw=(stage/'openroad-globalrouting.log').read_text()
        result['returncode']=process.returncode
        result['native_congestion']=routing.parse_congestion(raw)
        overflow=result['native_congestion'][-1]['total_overflow']
        result['original_resources_identical'] = {row['layer']:row['resource'] for row in result['native_congestion'][:-1]} == {
                'Metal1':16596,'Metal2':27616,'Metal3':34082,'Metal4':26432}
        if not result['original_resources_identical'] and reduced_nets is None:
            raise ValueError('Original per-layer resources changed')
        result['diagnostic_reduced_nets'] = reduced_nets
        result['native_global_route_passed']=process.returncode==0 and overflow==0
        if overflow:
            if process.returncode==0 or 'GRT-0116' not in (stage/'native-return.txt').read_text():
                raise ValueError('Native congestion failure not retained')
        elif process.returncode!=0:
            raise ValueError('Zero overflow still has native routing error')
        if iterations==50:
            if overflow!=133:
                raise ValueError('Replay no longer reproduces133')
            if cfg.sha(stage/'native-congestion.rpt')!=REPORT_SHA:
                raise ValueError('Replay markers differ from measured control')
        if re.findall(r'(?m)^\+ global_route -congestion_iterations (\d+)\b',raw)!=[str(iterations)]:
            raise ValueError('Native routing budget/call count differs')
        resolved=json.loads((stage/'config.json').read_text())
        validate_native_policy(resolved,config,original)
        if resolved['CELL_LIBS']!=config['LIB'] or cfg.macro_contract(resolved['MACROS'])!=cfg.macro_contract(config['MACROS']):
            raise ValueError('Native library/macro differs')
        summary=parse_segments((stage/'native-segments.txt').read_text())
        (OUT/'target-segments.json').write_text(json.dumps(summary,indent=2)+'\n')
        result['segments_sha256']=cfg.sha(stage/'native-segments.txt')
        result['targets_sha256']=cfg.sha(OUT/'target-segments.json')
        if iterations==50:
            validate_trace_hashes(result['segments_sha256'], result['targets_sha256'])
        result['final_route_segments_exact']=result['segments_sha256']==SEGMENTS_SHA and result['targets_sha256']==TARGETS_SHA
        if re.findall(r'(?m)^\+ set_debug_level GRT grtSteps (\d+)\b',raw)!=['1']:
            raise ValueError('Native scalar debug command missing or repeated')
        result['stage_scalars']=parse_stage_scalars(raw)
        if re.findall(r'(?m)^\+ set_debug_level GRT congestionIterations (\d+)\b',raw)!=['1']:
            raise ValueError('Native iteration debug command missing or repeated')
        result['negotiation_epochs']=parse_negotiation_epochs(raw)
        result['native_net_count']=summary['native_net_count']
        authenticate()
        result['source_unchanged']=True
        result['diagnostic_completed']=True
    except Exception as exc:
        result['error']=str(exc)
        raise
    finally:
        (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--inside':
        reports.instrument=instrument
        # Preserve the base copying routine rather than recursively dispatching.
        reports.inside(*(Path(x) for x in sys.argv[2:]))
    else:main()

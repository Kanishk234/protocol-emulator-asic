"""Exact best133 replay with failed-route segment export; no acceptance waiver."""
import json
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
PREVIOUS = ROOT / 'build/route_trace_input/previous'
OUT = ROOT / 'build/route_trace'
TARGETS = {'cell_val[30]', 'cell_pad[27]', 'cell_pad[31]', 'cell_val[27]'}
BASE_INSTRUMENT = reports.instrument
REPORT_SHA = '8e2f5c5003e495d3d347be7d593bb4bbc7801723db2902c3cb530e70a157a1df'
SDC_SHA = '2fd4e213532d83ee258899b6fc1ed48c4e5d91ddb0ccbe21eea0226cc90fd56e'
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
    modified = original.replace(reports.COMMAND, TRACE)
    if modified.replace(TRACE, reports.COMMAND, 1) != original:
        raise ValueError('Unexpected observer mutation')
    copied.write_text(modified)
    hashes = json.loads((directory / 'source-sha256.json').read_text())
    hashes['trace_common'] = cfg.sha(copied)
    (directory / 'source-sha256.json').write_text(json.dumps(hashes, indent=2)+'\n')
    with (directory / 'ATTRIBUTION.md').open('a') as f:
        f.write('Observer additionally exports raw segments after native routing, then rethrows its original failure.\n')
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


def authenticate():
    for name,digest in payload.EXPECTED.items():
        if cfg.sha(SOURCE/name) != digest: raise ValueError('Best133 source differs: '+name)
    if cfg.sha(SOURCE/'result.json') != '28739ad6b5379ef6ed299d1b5c613b577c8059be9807a3e407c179dca74a48cb':
        raise ValueError('Producer result differs')


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise ValueError('Native replay only on hosted runner')
    OUT.mkdir(exist_ok=False)
    result={'diagnostic_completed':False,'physical_acceptance':False,'route_passed':False,
            'source_run':38167697696,'reference_route_run':38453870785}
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
        previous=PREVIOUS/'ten_buffers/1-openroad-globalrouting/config.json'
        if cfg.sha(previous)!=routing.ORIGINAL_ROUTING_CONFIG_SHA:raise ValueError('Original routing policy differs')
        original=json.loads(previous.read_text())
        config,protected=routing.configure_iterations(config,original,50)
        result['protected_routing_settings']=protected
        path=OUT/'config.json';path.write_text(json.dumps(config))
        sdc=SOURCE/'padded_sta_nom_typ_1p20V_25C/final/sdc/tt_um_warp.sdc'
        if cfg.sha(sdc)!=SDC_SHA:raise ValueError('Source SDC differs')
        state=OUT/'state.json';state.write_text(json.dumps({'odb':str(SOURCE/'padded.odb'),
            'nl':str(SOURCE/'padded.nl.v'),'sdc':str(sdc),'metrics':{}}))
        run=OUT/'replay';run.mkdir()
        cmd=['docker','run','--rm','-v',f'{ROOT}:{ROOT}','-w',str(ROOT),'-e',
            f"PDK_ROOT={os.environ['PDK_ROOT']}",'--entrypoint','python3',cfg.IMAGE,
            str(Path(__file__).resolve()),'--inside',str(path),str(state),str(run)]
        with (OUT/'replay.log').open('w') as log:
            process=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=900)
        stage,=run.glob('*-openroad-globalrouting')
        raw=(stage/'openroad-globalrouting.log').read_text()
        result['returncode']=process.returncode
        result['native_congestion']=routing.parse_congestion(raw)
        if not result['native_congestion'] or result['native_congestion'][-1]['total_overflow']!=133:
            raise ValueError('Replay no longer reproduces133')
        if cfg.sha(stage/'native-congestion.rpt')!=REPORT_SHA:
            raise ValueError('Replay markers differ from measured control')
        if process.returncode==0 or 'GRT-0116' not in (stage/'native-return.txt').read_text():
            raise ValueError('Original native failure not retained')
        if re.findall(r'(?m)^\+ global_route -congestion_iterations (\d+)\b',raw)!=['50']:
            raise ValueError('Native routing budget/call count differs')
        resolved=json.loads((stage/'config.json').read_text())
        validate_native_policy(resolved,config,original)
        if resolved['CELL_LIBS']!=config['LIB'] or cfg.macro_contract(resolved['MACROS'])!=cfg.macro_contract(config['MACROS']):
            raise ValueError('Native library/macro differs')
        summary=parse_segments((stage/'native-segments.txt').read_text())
        (OUT/'target-segments.json').write_text(json.dumps(summary,indent=2)+'\n')
        result['segments_sha256']=cfg.sha(stage/'native-segments.txt')
        result['targets_sha256']=cfg.sha(OUT/'target-segments.json')
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

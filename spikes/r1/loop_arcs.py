"""Read-only arc/constant reports for the exact original eight structural loops."""
import argparse
import json
from pathlib import Path
import re

from boolean_support import sha
from run_timing import compare,parse_log

NATIVE_SHA='64922d92969e229e8562d9cc0c4bd1cb5add15766ec10709576f0255ebf2ce06'


def loop_cells(text):
    marker='Warning: There are 8 combinational loops in the design.'
    if text.count(marker)!=1:
        raise ValueError('Require original eight-loop report')
    body=text.split(marker,1)[1]
    cells=sorted({cell for cell,pin in re.findall(r'^  (Tile_X\d+Y\d+_[^/\s]+/[^/\s]+)/([^/\s]+)\s*$',body,re.M)})
    if len(cells)!=23:
        raise ValueError('Original loop-cell coverage differs')
    return cells


def render_trace(cells,modules,top):
    lines=['puts "R1_LOOP_ARCS_BEGIN"'];pairs=[]
    for full in cells:
        tile,name=full.split('/')
        cell=modules[top['cells'][tile]['type']]['cells'][name]
        outputs=[p for p,d in cell['port_directions'].items() if d=='output']
        if len(outputs)!=1 or re.search(r'_(?:df|dl)',cell['type']):
            raise ValueError('Unexpected loop cell kind')
        if any(len(bits)!=1 for bits in cell['connections'].values()):
            raise ValueError('Non-scalar loop cell pin')
        lines.extend([f'puts "R1_LOOP_CELL {full}"',f'sta::report_constant {{{full}}}'])
        for pin,direction in cell['port_directions'].items():
            if direction!='input':continue
            key=full+'/'+pin+'->'+outputs[0];pairs.append(key)
            lines.extend([f'puts "R1_LOOP_ARC {key}"',
                f'sta::report_edges -from {{{full}/{pin}}} -to {{{full}/{outputs[0]}}}'])
    lines.append('puts "R1_LOOP_ARCS_END"')
    return '\n'.join(lines)+'\n',pairs


def prepare(capsule,native_dir,out):
    capsule,native_dir,out=(Path(p).resolve() for p in (capsule,native_dir,out))
    native=native_dir/'all-native.json';top=capsule/'analysis/top.json';log=capsule/'analysis/static.log'
    if sha(native)!=NATIVE_SHA:raise ValueError('Native export identity differs')
    cells=loop_cells(log.read_text())
    trace,pairs=render_trace(cells,json.loads(native.read_text())['modules'],json.loads(top.read_text())['modules']['eFPGA'])
    out.mkdir(parents=True,exist_ok=False)
    inputs=[Path(__file__),Path(__file__).with_name('run_timing.py'),native,top,log]
    scripts={}
    for policy in ('static','dynamic'):
        source=native_dir/('control_'+policy+'.tcl');inputs.append(source)
        text=source.read_text()
        if text.count('puts "RUNSTA_END"')!=1:raise ValueError('Missing original completion marker')
        path=out/(policy+'.tcl');path.write_text(text.replace('puts "RUNSTA_END"',trace+'puts "RUNSTA_END"'))
        scripts[str(path)]=sha(path)
    (out/'plan.json').write_text(json.dumps(dict(cells=cells,pairs=pairs,
        input_sha256={str(p):sha(p) for p in inputs},scripts_sha256=scripts),indent=2)+'\n')


def audit(out):
    out=Path(out).resolve();plan=json.loads((out/'plan.json').read_text())
    for name,digest in {**plan['input_sha256'],**plan['scripts_sha256']}.items():
        if sha(name)!=digest:raise ValueError('Loop observation input changed')
    logs=[]
    for policy in ('static','dynamic'):
        text=(out/(policy+'.log')).read_text();logs.append(parse_log(text))
        if text.count('R1_LOOP_ARCS_BEGIN')!=1 or text.count('R1_LOOP_ARCS_END')!=1:
            raise ValueError('Incomplete loop observation')
        observed=re.findall(r'^R1_LOOP_ARC (.+)$',text,re.M)
        if observed!=plan['pairs']:raise ValueError('Missing, duplicate or reordered loop arc coverage')
    timing=compare(*logs)
    if len(timing['loop_policy_differences'])!=6 or abs(timing['worst_slack_ns']-1.508933)>1e-6:
        raise ValueError('Original timing control differs')
    (out/'result.json').write_text(json.dumps(dict(diagnostic_complete=True,loop_cells=len(plan['cells']),
        observed_pin_pairs=len(plan['pairs']),original_timing=timing,timing_acceptance=False,
        physical_acceptance=False,scope='Read-only reports of the original loop cells. No added case, disabled arc, netlist/model change or timing qualification.'),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    prep=sub.add_parser('prepare')
    for name in ('capsule','native-dir','out'):prep.add_argument('--'+name,type=Path,required=True)
    sub.add_parser('audit').add_argument('--out',type=Path,required=True)
    args=vars(p.parse_args());mode=args.pop('mode');(prepare if mode=='prepare' else audit)(**args)

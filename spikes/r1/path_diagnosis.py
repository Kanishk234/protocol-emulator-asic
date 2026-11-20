"""Expand authenticated failing timing paths without changing timing constraints."""
import argparse
import json
from pathlib import Path

from assembly_catalog import sha
from routed_timing import prepare as prepare_parent, run as run_parent
from run_timing import parse_log


def partition(endpoints, registers, ports):
    internal = {name+'/D' for name in registers}
    if internal & set(ports):
        raise ValueError('Ambiguous endpoint identity')
    groups = dict(internal_register=[], macro_output=[])
    for name, slack in endpoints.items():
        if name in internal:
            group = 'internal_register'
        elif name in ports and ports[name]['direction'] == 'output':
            group = 'macro_output'
        else:
            raise ValueError('Unknown timing endpoint: '+name)
        groups[group].append(dict(endpoint=name, slack_ns=slack))
    return {k:dict(count=len(v), negative_count=sum(r['slack_ns']<0 for r in v),
                   worst=sorted(v,key=lambda r:r['slack_ns'])[:20]) for k,v in groups.items()}


def prepare(rc, proof, native, capsule, pdk, out):
    out=Path(out).resolve()
    prepare_parent(rc,proof,native,capsule,pdk,out)
    plan=json.loads((out/'plan.json').read_text())
    ports=json.loads((Path(proof)/'analysis.json').read_text())['modules']['warp_r1_candidate']['ports']
    plan['diagnostic_ports']=ports
    plan['input_sha256'][str(Path(__file__).resolve())]=sha(__file__)
    for label in plan['rendered_sha256']:
        if label.startswith('cell_control'):continue
        script=out/(label+'.tcl');text=script.read_text()
        delay='min' if 'hold' in label else 'max'
        reports=[]
        for name,source,dest in (
            ('register_to_register','[all_registers -edge_triggered -clock run -clock_pins]','[all_registers -edge_triggered -clock run -data_pins]'),
            ('input_to_register','[all_inputs]','[all_registers -edge_triggered -clock run -data_pins]'),
            ('register_to_output','[all_registers -edge_triggered -clock run -clock_pins]','[all_outputs]')):
            reports += ['puts "R1_DETAIL_BEGIN '+name+'"',
                        'report_checks -from '+source+' -to '+dest+' -path_delay '+delay+
                        ' -format full_clock_expanded -group_path_count 10 -digits 6',
                        'puts "R1_DETAIL_END '+name+'"']
        if text.count('puts "RUNSTA_END"')!=1:raise ValueError('Unexpected completion marker')
        text=text.replace('puts "RUNSTA_END"','\n'.join(reports)+'\nputs "RUNSTA_END"')
        script.write_text(text);plan['rendered_sha256'][label]=sha(script)
    (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')


def run(out):
    out=Path(out).resolve()
    try:run_parent(out)
    except SystemExit:pass
    baseline=json.loads((out/'result.json').read_text())
    if not baseline['diagnostic_complete'] or baseline.get('error')!='Configured macro setup/hold or loop-policy check fails':
        raise ValueError('Original failing timing diagnostic did not reproduce')
    if any(not row['passed'] for name,row in baseline['annotation'].items() if name.startswith('routed_')):
        raise ValueError('Incomplete active annotation')
    plan=json.loads((out/'plan.json').read_text());groups={}
    for kind,expected in (('setup',-11.108903),('hold',-1.870506)):
        model=baseline['models']['routed_'+kind]
        if model['loop_policy_sensitive'] or model['structural_loops'] or abs(model['worst_slack_ns']-expected)>1e-6:
            raise ValueError('Original timing model changed')
        for policy in ('static','dynamic'):
            label='routed_'+kind+'_'+policy;text=(out/(label+'.log')).read_text()
            for name in ('register_to_register','input_to_register','register_to_output'):
                if text.count('R1_DETAIL_BEGIN '+name+'\n')!=1 or text.count('R1_DETAIL_END '+name+'\n')!=1:
                    raise ValueError('Missing expanded path evidence')
            parsed=parse_log(text)
            groups[label]=partition(parsed['endpoints'],parsed['ffs'],plan['diagnostic_ports'])
        if groups['routed_'+kind+'_static']!=groups['routed_'+kind+'_dynamic']:
            raise ValueError('Endpoint partition differs between loop policies')
    result=dict(run=baseline['run'],source_sha=baseline['source_sha'],diagnostic_complete=True,
                timing_acceptance=False,physical_acceptance=False,groups=groups,
                scope='Additional path reports on the unchanged authenticated failing macro model. Internal endpoint means capture inside macro; launch can still be an external input. Expanded reports distinguish launch classes. No boundary waiver or full-chip acceptance.')
    (out/'path-diagnosis.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('prepare')
    for name in ('rc','proof','native','capsule','pdk','out'):p.add_argument('--'+name,type=Path,required=True)
    sub.add_parser('run').add_argument('--out',type=Path,required=True)
    args=vars(parser.parse_args());mode=args.pop('mode');(prepare if mode=='prepare' else run)(**args)

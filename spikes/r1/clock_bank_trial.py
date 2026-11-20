"""Keep the proven SPI source fixed and constrain only its global clock bank."""
import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess

from assembly_catalog import sha
from fixed_relocation import logical_graph


def prepare(capsule,trial,current,out):
    capsule,trial,current,out=(Path(p).resolve() for p in (capsule,trial,current,out))
    resource=capsule/'model/resource';desc=json.loads((resource/'resource-control.json').read_text())
    if any(sha(resource/p)!=h for p,h in desc['generated_sha256'].items()):raise ValueError('Frozen resource changed')
    native=json.loads((current/'sa_functional/result.json').read_text());timing=json.loads((current/'r1_loop_timing/result.json').read_text())
    if (str(native['run'])!='44802619585' or not native['passed'] or not timing['model_qualified'] or
            timing['models']['setup']['inactive_unobservable']!=0 or timing['models']['setup']['edge_registers']!=370):
        raise ValueError('Require measured native pass and all-clocked negative timing control')
    source=trial/'candidate';row=json.loads((source/'result.json').read_text())
    if str(row['run'])!='44798802734' or sha(source/'concurrency.wbit')!='79db28f92959f998faf2b6b00b65be3539abc5e03625f77bd80584601fa2fd6a':
        raise ValueError('Proven SPI compiler source changed')
    design=json.loads((source/'design.json').read_text());module=design['modules']['warp_top']
    cells=[n for n,c in module['cells'].items() if c['type']=='GBUF']
    placed=json.loads((source/'design_pnr.json').read_text())['modules']['top']
    if len(cells)!=1 or placed['cells'][cells[0]]['attributes']['NEXTPNR_BEL']!='X0Y4/A':
        raise ValueError('Measured clock-bank source changed')
    pinned=copy.deepcopy(design);attrs=pinned['modules']['warp_top']['cells'][cells[0]]['attributes']
    if 'NEXTPNR_BEL' in attrs or 'BEL_STRENGTH' in attrs:raise ValueError('Clock source already constrained')
    attrs['NEXTPNR_BEL']='X0Y4/D';attrs['BEL_STRENGTH']=format(6,'032b')
    if logical_graph(module)!=logical_graph(pinned['modules']['warp_top']):raise ValueError('Pinning changed logic')
    out.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(source/'design.json',out/'control.json');(out/'candidate.json').write_text(json.dumps(pinned)+'\n')
    bound=[Path(__file__).resolve(),source/'result.json',source/'design.json',source/'design_pnr.json',source/'pins.pcf',
        source/'report.json',source/'concurrency.wbit',resource/'resource-control.json',*[resource/p for p in desc['generated_sha256']],
        current/'sa_functional/result.json',current/'r1_loop_timing/result.json',out/'control.json',out/'candidate.json']
    (out/'plan.json').write_text(json.dumps(dict(resource=str(resource),source=str(source),clock_cell=cells[0],
        inputs={str(p):sha(p) for p in bound},scope='Same proven SPI source, pins, seed1, model,50MHz request. Only candidate GBUF placement is USER-locked to original clock bank D; user-cell placement/routes may change. No transplanted image repairs or timing/hardware acceptance.'),indent=2)+'\n')


def run(out):
    from compile import compile as compiler
    from compile.bitfile import BitFile
    from compile.bitgen import gen_words
    from cloud_arch_comparison import run_bounded
    if os.environ.get('GITHUB_ACTIONS')!='true':raise ValueError('Heavy clock-bank routing runs hosted')
    out=Path(out).resolve();plan=json.loads((out/'plan.json').read_text())
    if any(sha(p)!=h for p,h in plan['inputs'].items()):raise ValueError('Frozen clock trial inputs changed')
    binary=compiler.tool('nextpnr-generic')
    if sha(binary)!='a36179428d1afb5c9b88950097f03473f22949a39be1ac5cf6e5f3a95b526829':raise ValueError('Unpinned nextpnr binary')
    resource,source=Path(plan['resource']),Path(plan['source']);result=dict(run=os.environ.get('GITHUB_RUN_ID'),source_sha=os.environ.get('GITHUB_SHA'),cases={},diagnostic_complete=False,timing_acceptance=False,physical_acceptance=False,adopted=False,scope=plan['scope'])
    control_graph=None
    try:
        for name,bank in (('control','X0Y4/A'),('candidate','X0Y4/D')):
            folder=out/name;folder.mkdir()
            command=[binary,'--uarch','fabulous','--json',str(out/(name+'.json')),'--write',str(folder/'design_pnr.json'),
                '-o','fasm='+str(folder/'design.fasm'),'-o','pcf='+str(source/'pins.pcf'),'-o','corner='+compiler.SLOW_CORNER,
                '--seed','1','--freq','50','--timing-allow-fail','--log',str(folder/'pnr.log')]
            previous=os.environ.get('FAB_ROOT');os.environ['FAB_ROOT']=str(resource/'macro/fabulous')
            try:run_bounded(command,folder/'stdout.log')
            finally:
                if previous is None:os.environ.pop('FAB_ROOT',None)
                else:os.environ['FAB_ROOT']=previous
            module=json.loads((folder/'design_pnr.json').read_text())['modules']['top'];clock=module['cells'][plan['clock_cell']]
            if clock['attributes']['NEXTPNR_BEL']!=bank:raise ValueError('Clock bank constraint changed')
            graph=logical_graph(module)
            if name=='control':control_graph=graph
            elif graph!=control_graph:raise ValueError('Clock constraint changes logical graph')
            words=gen_words(folder/'design.fasm',resource/'macro/fabulous/bitStreamSpec.bin')
            image=folder/'concurrency.wbit';BitFile(0xfe,words).save(image)
            if name=='control' and image.read_bytes()!=(source/'concurrency.wbit').read_bytes():raise ValueError('Clock A control image did not reproduce')
            util,estimate=compiler.parse_pnr_log(folder/'pnr.log')
            if not util or any(v['used']>v['available'] for v in util.values()):raise ValueError('Invalid capacity')
            report=dict(params=json.loads((source/'report.json').read_text())['params'],provenance=dict(bitfile_sha256=sha(image),kind='Same proven SPI source with explicit clock-bank placement experiment',parent_report_sha256=sha(source/'report.json')))
            (folder/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            result['cases'][name]=dict(image_sha256=sha(image),clock_bank=bank,logical_graph_preserved=True,placed_utilisation=util,model_fmax_mhz=estimate,model_timing_characterized=False)
        if result['cases']['control']['placed_utilisation']!=result['cases']['candidate']['placed_utilisation']:raise ValueError('Resource usage changed')
        result['diagnostic_complete']=True
    except Exception as exc:result['error']=str(exc);raise
    finally:(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    x=sub.add_parser('prepare')
    for name in ('capsule','trial','current','out'):x.add_argument('--'+name,type=Path,required=True)
    sub.add_parser('run').add_argument('--out',type=Path,required=True)
    a=vars(p.parse_args());mode=a.pop('mode');(prepare if mode=='prepare' else run)(**a)

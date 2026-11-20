"""Fixed-placement rerouting and one evidence-directed combinational LC move."""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess

from assembly_catalog import sha


def logical_graph(module):
    nets={};constants=[]
    for name,cell in module['cells'].items():
        for pin,bits in cell['connections'].items():
            for index,bit in enumerate(bits):
                terminal=(name,pin,index)
                if isinstance(bit,str):constants.append((terminal,bit))
                else:nets.setdefault(bit,[]).append(terminal)
    return dict(cells={n:dict(type=c['type'],parameters=c['parameters'],
                             directions={p:d for p,d in c['port_directions'].items() if c['connections'].get(p)})
                       for n,c in module['cells'].items()},
                nets=sorted(tuple(sorted(v)) for v in nets.values()),constants=sorted(constants))


def prepare(capsule,out):
    capsule,out=Path(capsule).resolve(),Path(out).resolve()
    case=capsule/'model/compile/uart_spi_11';source=case/'design_pnr.json'
    design=json.loads(source.read_text());module=design['modules']['top']
    original={n:c['attributes']['NEXTPNR_BEL'] for n,c in module['cells'].items()}
    matches=[n for n,b in original.items() if b=='X1Y2/F']
    if len(matches)!=1 or 'X1Y1/C' in original.values():raise ValueError('Original source/free target placement changed')
    moved=matches[0];cell=module['cells'][moved]
    if (cell['type']!='FABULOUS_LC' or cell['parameters']!={'INIT':'0001000100010001'} or
            set(cell['connections'])!={'I0','I1','I2','I3','O'} or cell['connections']['I2'] or cell['connections']['I3']):
        raise ValueError('Require the measured combinational two-input LUT with no carry or FF')
    out.mkdir(parents=True,exist_ok=False)
    variants={}
    for name in ('restore','reroute','candidate'):
        derived=copy.deepcopy(design)
        if name!='restore':
            for net in derived['modules']['top']['netnames'].values():net.get('attributes',{}).pop('ROUTING',None)
            # Pinned nextpnr PlaceStrength::STRENGTH_USER=6. Keep placement
            # execution for FABulous prePlace timing/tag initialization.
            for item in derived['modules']['top']['cells'].values():
                item['attributes']['BEL_STRENGTH']=format(6,'032b')
        placements=dict(original)
        if name=='candidate':
            placements[moved]='X1Y1/C';derived['modules']['top']['cells'][moved]['attributes']['NEXTPNR_BEL']='X1Y1/C'
        if logical_graph(derived['modules']['top'])!=logical_graph(module):raise ValueError('Logical graph changed')
        folder=out/name;folder.mkdir();path=folder/'input.json';path.write_text(json.dumps(derived)+'\n')
        variants[name]=dict(input_sha256=sha(path),placements=placements)
    resource=capsule/'model/resource';desc=json.loads((resource/'resource-control.json').read_text())
    bound=[Path(__file__).resolve(),source,case/'concurrency.wbit',case/'report.json',
           *[resource/p for p in desc['generated_sha256']]]
    if any(sha(resource/p)!=h for p,h in desc['generated_sha256'].items()):raise ValueError('Frozen resource model changed')
    (out/'plan.json').write_text(json.dumps(dict(capsule=str(capsule),variants=variants,moved_cell=moved,
        input_sha256={str(p):sha(p) for p in bound},
        scope='Restore exact original image; then compare identical fixed placements rerouted from scratch versus one combinational LC moved X1Y2/F to free X1Y1/C. Same logical graph, seed1, 50MHz and hardware. No characterized timing or adoption.'),indent=2)+'\n')


def run(out):
    from compile import compile as compiler
    from compile.bitfile import BitFile
    from compile.bitgen import gen_words
    from cloud_arch_comparison import run_bounded
    if os.environ.get('GITHUB_ACTIONS')!='true':raise ValueError('Rerouting runs hosted')
    out=Path(out).resolve();plan=json.loads((out/'plan.json').read_text())
    if any(sha(p)!=h for p,h in plan['input_sha256'].items()):raise ValueError('Frozen relocation inputs changed')
    cap=Path(plan['capsule']);case=cap/'model/compile/uart_spi_11';resource=cap/'model/resource'
    binary=compiler.tool('nextpnr-generic')
    version=subprocess.check_output([binary,'--version'],stderr=subprocess.STDOUT,text=True)
    if 'nextpnr-0.11.1-34-gc4fbb55a' not in version:raise ValueError('Unpinned nextpnr')
    result=dict(run=os.environ.get('GITHUB_RUN_ID'),source_sha=os.environ.get('GITHUB_SHA'),cases={},
                diagnostic_complete=False,timing_acceptance=False,physical_acceptance=False,adopted=False,scope=plan['scope'])
    try:
        for name,row in plan['variants'].items():
            folder=out/name
            if sha(folder/'input.json')!=row['input_sha256']:raise ValueError('Fixed placement input changed')
            command=[binary,'--uarch','fabulous','--json',str(folder/'input.json'),'--write',str(folder/'design_pnr.json'),
                '--no-pack','--seed','1','--freq','50','--timing-allow-fail',
                '-o','corner='+compiler.SLOW_CORNER,'-o','fasm='+str(folder/'design.fasm'),'--log',str(folder/'pnr.log')]
            if name=='restore':command+=['--no-place']
            prior=os.environ.get('FAB_ROOT');os.environ['FAB_ROOT']=str(resource/'macro/fabulous')
            try:run_bounded(command,folder/'stdout.log')
            finally:
                if prior is None:os.environ.pop('FAB_ROOT',None)
                else:os.environ['FAB_ROOT']=prior
            actual=json.loads((folder/'design_pnr.json').read_text())['modules']['top']
            original=json.loads((case/'design_pnr.json').read_text())['modules']['top']
            if logical_graph(actual)!=logical_graph(original):raise ValueError('Rerouting changed logical graph')
            if {n:c['attributes']['NEXTPNR_BEL'] for n,c in actual['cells'].items()}!=row['placements']:
                raise ValueError('Unexpected cell placement change')
            image=folder/'concurrency.wbit';BitFile(0xFE,gen_words(folder/'design.fasm',resource/'macro/fabulous/bitStreamSpec.bin')).save(image)
            if name=='restore' and image.read_bytes()!=(case/'concurrency.wbit').read_bytes():
                raise ValueError('Original checkpoint image did not restore exactly')
            util,estimate=compiler.parse_pnr_log(folder/'pnr.log')
            report=dict(params=json.loads((case/'report.json').read_text())['params'],provenance=dict(
                bitfile_sha256=sha(image),kind='Source-bound fixed placement rerouting diagnostic',plan_sha256=sha(out/'plan.json')))
            (folder/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            result['cases'][name]=dict(image_sha256=sha(image),model_fmax_mhz=estimate,model_timing_characterized=False,
                placed_utilisation=util,logical_graph_preserved=True,placements_exact=True,actually_loaded=False)
            (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        result['diagnostic_complete']=True
    except Exception as exc:
        result['error']=str(exc);raise
    finally:(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('prepare')
    for name in ('capsule','out'):p.add_argument('--'+name,type=Path,required=True)
    sub.add_parser('run').add_argument('--out',type=Path,required=True)
    args=vars(parser.parse_args());mode=args.pop('mode');(prepare if mode=='prepare' else run)(**args)

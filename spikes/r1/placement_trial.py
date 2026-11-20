"""Bounded fixed-seed placement trials on frozen primary RTL.

The model is not characterized timing. Fresh physical configured timing
and actual native loading remain mandatory before adopting any resulting image.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess

from assembly_catalog import sha


def admit_frequency_log(text, target):
    if 'at '+format(target,'.2f')+' MHz)' not in text:
        raise ValueError('Native requested placement frequency did not reproduce')


def prepare(capsule,out,strategy='frequency'):
    if strategy not in ('frequency','sa'):raise ValueError('Unknown bounded placement strategy')
    capsule,out=Path(capsule).resolve(),Path(out).resolve()
    original=capsule/'model/resource';description=json.loads((original/'resource-control.json').read_text())
    if description['radix']!='radix8_2':raise ValueError('Require frozen reduced-radix model')
    for name,digest in description['generated_sha256'].items():
        if sha(original/name)!=digest:raise ValueError('Changed frozen generator output')
    out.mkdir(parents=True,exist_ok=False)
    case=capsule/'model/compile/uart_spi_11'
    paths=[Path(__file__).resolve(),case/'design.json',case/'pins.pcf',case/'design.fasm',case/'concurrency.wbit',
           case/'report.json',original/'resource-control.json',*[original/name for name in description['generated_sha256']]]
    change=('Reproduce implicit 12 MHz control, then explicitly request 50 MHz.' if strategy=='frequency'
            else 'Both cases explicitly request 50 MHz; candidate changes only placer from default HeAP/refinement to full SA.')
    (out/'plan.json').write_text(json.dumps(dict(capsule=str(capsule),original_model=str(original),strategy=strategy,
        inputs={str(p):sha(p) for p in paths},
        scope='Fixed seed1, original synthesized design/pins/model and routing budget. '+change+' Placeholder model remains uncharacterized; no timing or physical acceptance.'),indent=2)+'\n')


def run(out):
    from compile import compile as compiler
    from compile.bitfile import BitFile
    from compile.bitgen import gen_words
    from cloud_arch_comparison import run_bounded
    if os.environ.get('GITHUB_ACTIONS')!='true':raise ValueError('Heavy placement trial runs hosted')
    out=Path(out).resolve();plan=json.loads((out/'plan.json').read_text())
    if any(sha(p)!=h for p,h in plan['inputs'].items()):raise ValueError('Frozen trial input changed')
    binary=compiler.tool('nextpnr-generic')
    version=subprocess.check_output([binary,'--version'],stderr=subprocess.STDOUT,text=True)
    if 'nextpnr-0.11.1-34-gc4fbb55a' not in version:raise ValueError('Unpinned nextpnr')
    case=Path(plan['capsule'])/'model/compile/uart_spi_11'
    result=dict(run=os.environ.get('GITHUB_RUN_ID'),source_sha=os.environ.get('GITHUB_SHA'),
                scope=plan['scope'],nextpnr_version=version,binary_sha256=sha(binary),cases={},
                diagnostic_complete=False,timing_acceptance=False,physical_acceptance=False,adopted=False)
    try:
        strategy=plan.get('strategy','frequency')
        if strategy not in ('frequency','sa'):raise ValueError('Unknown bounded placement strategy')
        for name,target in [('control',50 if strategy=='sa' else 12),('candidate',50)]:
            resource=Path(plan['original_model'])
            folder=out/name;folder.mkdir()
            command=[binary,'--uarch','fabulous','--json',str(case/'design.json'),'--write',str(folder/'design_pnr.json'),
                '-o','fasm='+str(folder/'design.fasm'),'-o','pcf='+str(case/'pins.pcf'),
                '-o','corner='+compiler.SLOW_CORNER,'--seed','1','--log',str(folder/'pnr.log'),'--timing-allow-fail']
            if target==50:command+=['--freq','50']
            if name=='candidate' and strategy=='sa':command+=['--placer','sa']
            # run_bounded starts a dedicated process group and kills all children on timeout.
            prior=os.environ.get('FAB_ROOT');os.environ['FAB_ROOT']=str(resource/'macro/fabulous')
            try:run_bounded(command,folder/'stdout.log')
            finally:
                if prior is None:os.environ.pop('FAB_ROOT',None)
                else:os.environ['FAB_ROOT']=prior
            admit_frequency_log((folder/'pnr.log').read_text(),target)
            words=gen_words(folder/'design.fasm',resource/'macro/fabulous/bitStreamSpec.bin')
            image=folder/'concurrency.wbit';BitFile(0xFE,words).save(image)
            if name=='control' and image.read_bytes()!=(case/'concurrency.wbit').read_bytes():
                raise ValueError('Original same-seed PNR control image did not reproduce')
            util,estimate=compiler.parse_pnr_log(folder/'pnr.log')
            if not util or any(r['used']>r['available'] for r in util.values()):raise ValueError('Invalid usage')
            report=dict(params=json.loads((case/'report.json').read_text())['params'],
                provenance=dict(bitfile_sha256=sha(image),kind='Diagnostic re-placement of frozen synthesized primary design',
                                parent_report_sha256=sha(case/'report.json'),trial_plan_sha256=sha(out/'plan.json')))
            (folder/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            result['cases'][name]=dict(image_sha256=sha(image),placed_utilisation=util,
                requested_placement_frequency_mhz=target,model_fmax_mhz=estimate,
                model_timing_characterized=False,actual_native_loading=False)
        result['diagnostic_complete']=True
    except Exception as exc:
        result['error']=str(exc);raise
    finally:(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('prepare');p.add_argument('--capsule',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--strategy',choices=('frequency','sa'),default='frequency')
    sub.add_parser('run').add_argument('--out',type=Path,required=True)
    args=vars(parser.parse_args());mode=args.pop('mode');(prepare if mode=='prepare' else run)(**args)

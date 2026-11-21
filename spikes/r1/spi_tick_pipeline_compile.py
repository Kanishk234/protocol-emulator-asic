"""Fresh fixed-seed R1 compilation, gated on eight SPI equivalence/test cases."""
import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import yaml

from assembly_catalog import sha
from spi_tick_pipeline_trial import SOURCE_SHA,admit_status,variant
from fixed_relocation import logical_graph
from compile.bitfile import BitFile
ROOT=Path(__file__).resolve().parents[2]



def pin_global_clock(design):
    pinned=copy.deepcopy(design)
    module=pinned['modules']['warp_top']
    clocks=[n for n,c in module['cells'].items() if c['type']=='GBUF']
    if len(clocks)!=1:raise ValueError('Require one global user clock')
    attrs=module['cells'][clocks[0]].setdefault('attributes',{})
    if 'NEXTPNR_BEL' in attrs or 'BEL_STRENGTH' in attrs:
        raise ValueError('Clock source already has placement constraints')
    attrs['NEXTPNR_BEL']='X0Y4/D';attrs['BEL_STRENGTH']=format(6,'032b')
    if logical_graph(module)!=logical_graph(design['modules']['warp_top']):
        raise ValueError('Clock placement constraint changes logic')
    return pinned,clocks[0]


def prepare(capsule,proofs,out):
    from autonomy.check_xml import check_xml
    capsule,proofs,out=(Path(p).resolve() for p in (capsule,proofs,out))
    resource=capsule/'model/resource';desc=json.loads((resource/'resource-control.json').read_text())
    if desc['radix']!='radix8_2' or any(sha(resource/p)!=h for p,h in desc['generated_sha256'].items()):
        raise ValueError('Frozen R1 resource changed')
    source=ROOT/'protocols/spi_ctrl/spi_ctrl_top.v'
    if sha(source)!=SOURCE_SHA:raise ValueError('SPI source changed')
    candidate=variant(source.read_text());seen=set();bound=[]
    import hashlib
    for folder in sorted(proofs.iterdir()):
        if not folder.is_dir():continue
        data=json.loads((folder/'result.json').read_text());identity=(data['mode'],data['half'])
        if identity in seen or not data['equivalence_passed'] or data['strict_source_tests']!=4:
            raise ValueError('Incomplete/duplicate SPI proof case')
        admit_status((folder/'equiv/status').read_text(),(folder/'proof.log').read_text())
        check_xml(folder/'results.xml',4)
        if sha(folder/'candidate/spi_ctrl_top.v')!=hashlib.sha256(candidate.encode()).hexdigest():
            raise ValueError('Proven candidate source differs')
        seen.add(identity);bound += [folder/'result.json',folder/'proof.log',folder/'equiv/status',folder/'results.xml',folder/'candidate/spi_ctrl_top.v']
    if seen!={(mode,half) for mode in range(4) for half in (4,25)}:raise ValueError('Require all eight proven and source-tested SPI configurations')
    parent=capsule/'model/compile/uart_spi_11';report=json.loads((parent/'report.json').read_text())
    for row in report['provenance']['inputs']:
        if '/protocols/' not in row['path']:continue
        path=ROOT/'protocols'/row['path'].split('/protocols/',1)[1]
        if not path.resolve().is_relative_to(ROOT/'protocols') or sha(path)!=row['sha256']:
            raise ValueError('Unchanged user protocol control differs from frozen source')
        bound.append(path)
    out.mkdir(parents=True,exist_ok=False);(out/'candidate-source').mkdir()
    (out/'candidate-source/spi_ctrl_top.v').write_text(candidate)
    shadow=out/'compiler-arch';shadow.mkdir();meta=yaml.safe_load((resource/'arch.yaml').read_text())
    meta['macro']=str(resource/'macro')
    (shadow/'arch.yaml').write_text(yaml.safe_dump(meta,sort_keys=False))
    shutil.copyfile(resource/'pins.csv',shadow/'pins.csv')
    # Only path relocation in a derived compiler descriptor, never the frozen resource.
    original=yaml.safe_load((resource/'arch.yaml').read_text());new=dict(meta);new['macro']=original['macro']
    if new!=original:raise ValueError('Compiler descriptor changes more than path relocation')
    bound += [Path(__file__).resolve(),ROOT/'spikes/r1/spi_tick_pipeline_trial.py',
              ROOT/'tools/compile/compile.py',ROOT/'tools/compile/bitgen.py',ROOT/'tools/compile/bitfile.py',
              ROOT/'test_internal/cloud_fresh_baseline.py',source,parent/'report.json',parent/'concurrency.wbit',
              resource/'resource-control.json',*[resource/p for p in desc['generated_sha256']],
              out/'candidate-source/spi_ctrl_top.v',shadow/'arch.yaml',shadow/'pins.csv']
    (out/'plan.json').write_text(json.dumps(dict(capsule=str(capsule),resource=str(resource),arch=str(shadow),
        inputs={str(p):sha(p) for p in bound},params=report['params'],
        scope='Source-proved registered SPI terminal pulse, same frozen physical fabric, pins, parameters, seed1 and50MHz request; candidate GBUF USER-pinned to original bank D. Compiler timing remains uncharacterized; no native, extracted timing or adoption claim.'),indent=2)+'\n')


def run(out,case):
    from compile import compile as compiler
    from cloud_fresh_baseline import specification
    if os.environ.get('GITHUB_ACTIONS')!='true' or case not in ('control','candidate'):
        raise ValueError('Fresh compilation runs hosted with explicit cases')
    out=Path(out).resolve();plan=json.loads((out/'plan.json').read_text())
    if any(sha(p)!=h for p,h in plan['inputs'].items()):raise ValueError('Frozen compile/proof input changed')
    version=subprocess.check_output([compiler.tool('yosys'),'-V'],text=True)
    if 'e74db6dea' not in version:raise ValueError('Yosys differs from the original primary compiler')
    np=subprocess.check_output([compiler.tool('nextpnr-generic'),'--version'],stderr=subprocess.STDOUT,text=True)
    if ('nextpnr-0.11.1-34-gc4fbb55a' not in np or
            sha(compiler.tool('nextpnr-generic'))!='a36179428d1afb5c9b88950097f03473f22949a39be1ac5cf6e5f3a95b526829'):
        raise ValueError('Unpinned nextpnr')
    pins,sources,params=specification('uart_spi_11')
    if params!=plan['params']:raise ValueError('Primary compile parameters changed')
    if case=='candidate':sources=[out/'candidate-source/spi_ctrl_top.v' if Path(p).resolve()==ROOT/'protocols/spi_ctrl/spi_ctrl_top.v' else p for p in sources]
    if case=='candidate':
        control=json.loads((out/'control/result.json').read_text())
        expected=Path(plan['capsule'])/'model/compile/uart_spi_11/concurrency.wbit'
        if control['case']!='control' or control['image_sha256']!=sha(expected) or control['source_sha']!=os.environ.get('GITHUB_SHA'):
            raise ValueError('Same-revision original compile control did not reproduce')
    original=compiler.run;clock_constraint=None
    def request_frequency(command,log,cwd,env=None):
        nonlocal clock_constraint
        if Path(command[0]).name=='nextpnr-generic':
            command=[*command,'--freq','50']
            if case=='candidate':
                index=command.index('--json')+1;source=Path(command[index])
                pinned,clock=pin_global_clock(json.loads(source.read_text()))
                target=out/case/'design_clock_d.json';target.write_text(json.dumps(pinned)+'\n')
                clock_constraint=dict(cell=clock,bel='X0Y4/D',logical_graph_preserved=True,
                    source_json_sha256=sha(source),pinned_json_sha256=sha(target))
                command[index]=str(target)
        return original(command,log,cwd,env)
    compiler.run=request_frequency
    try:image,report=compiler.compile_design(sources,pins,Path(plan['arch']),out/case,seed=1,set_params=params,strict_ports=True)
    finally:compiler.run=original
    if case=='control' and Path(image).read_bytes()!=(Path(plan['capsule'])/'model/compile/uart_spi_11/concurrency.wbit').read_bytes():
        raise ValueError('Original same-source compiler control image did not reproduce')
    if case=='candidate' and not (out/'control/result.json').is_file():raise ValueError('Original compile control missing')
    if case=='candidate':
        placed=json.loads((out/case/'design_pnr.json').read_text())['modules']['top']
        clocks=[c for c in placed['cells'].values() if c['type']=='GBUF']
        if clock_constraint is None or len(clocks)!=1 or clocks[0]['attributes']['NEXTPNR_BEL']!='X0Y4/D':
            raise ValueError('Candidate global clock constraint not honored')
    words=BitFile.load(image)
    if words.arch_version!=0xfe or len(words.words)!=962:raise ValueError('Wrong diagnostic image format')
    (out/case/'result.json').write_text(json.dumps(dict(case=case,run=os.environ.get('GITHUB_RUN_ID'),source_sha=os.environ.get('GITHUB_SHA'),
        image_sha256=sha(image),placed_utilisation=report['utilisation'],model_fmax_mhz=report['fmax_mhz'],model_timing_characterized=False,
        requested_placement_frequency_mhz=50,yosys_version=version,nextpnr_version=np,
        clock_constraint=clock_constraint,actual_native_loading=False,timing_acceptance=False,physical_acceptance=False,adopted=False),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    x=sub.add_parser('prepare')
    for name in ('capsule','proofs','out'):x.add_argument('--'+name,type=Path,required=True)
    x=sub.add_parser('run');x.add_argument('--out',type=Path,required=True);x.add_argument('--case',choices=('control','candidate'),required=True)
    a=vars(p.parse_args());mode=a.pop('mode');(prepare if mode=='prepare' else run)(**a)

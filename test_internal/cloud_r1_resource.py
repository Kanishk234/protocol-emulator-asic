"""Hosted oversized capacity control; fit/configuration only, never area/timing."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
sys.path.insert(0,str(ROOT/'test_internal'))
from compile import compile as compiler
from compile.bitfile import BitFile
from cloud_arch_comparison import run_bounded
from cloud_fresh_baseline import specification, SINGLES

PAIRS=('uart_spi_11','uart_i2c_11')
CASES=(*(name for name in SINGLES if name != 'i2c_target'), *PAIRS)


def failure_record(case, directory, error):
    path=Path(directory)/'pnr.log'
    diagnosis=dict(category='unobserved',fatal_messages=[],over_capacity=[],
                   advice='No native PNR log; this is not evidence of architecture nonfit.')
    if path.is_file():
        util,_=compiler.parse_pnr_log(path)
        diagnosis=compiler.diagnose_pnr_failure(path.read_text(errors='replace'),util)
    stage='unobserved'
    if path.is_file():
        text=path.read_text(errors='replace')
        if 'Info: Routing..' in text:
            stage='routing'
        elif 'placer' in text:
            stage='placement'
    return dict(case=case,status='failed',error=str(error)[:2000],native_diagnosis=diagnosis,
                failure_kind='timeout' if isinstance(error,subprocess.TimeoutExpired) else 'worker_failure',
                timeout_seconds=error.timeout if isinstance(error,subprocess.TimeoutExpired) else None,
                observed_stage=stage,
                physical_acceptance=False,timing_acceptance=False)


def worker(case, model, directory):
    if os.environ.get('GITHUB_ACTIONS')!='true' or case not in CASES:
        raise RuntimeError('Explicit resource-control case must run hosted')
    directory=Path(directory);directory.mkdir(exist_ok=False)
    pins,sources,params=specification(case)
    _,report=compiler.compile_design(sources,pins,Path(model),directory,seed=1,set_params=params,strict_ports=case in PAIRS)
    util,fmax=compiler.parse_pnr_log(directory/'pnr.log')
    if util!=report['utilisation'] or not util or any(v['used']>v['available'] for v in util.values()):
        raise ValueError('Native usage/report mismatch')
    if (report['params']!=params or report['arch']!='r1_resource_control'
            or (case in PAIRS and (report['unmapped_inputs_tied_0'] or report['unmapped_outputs_open']))
            or report['build_options']['seed']!=1):
        raise ValueError('Concurrent workload identity differs')
    for resource in ('wp_timer','wp_shift'):
        if (case in PAIRS and util[resource]['used']!=3) or util[resource]['available']!=4:
            raise ValueError('Incorrect hard primitive usage')
    images=list(directory.glob('*.wbit'))
    if len(images)!=1:raise ValueError('Missing/ambiguous image')
    image=BitFile.load(images[0])
    if image.arch_version!=0xFE or len(image.words)!=report['words'] or f'0x{image.crc:08X}'!=report['crc32']:
        raise ValueError('Incorrect diagnostic image')
    result=dict(case=case,params=params,seed=1,placed_utilisation=util,words=len(image.words),
                synthesis_estimate=compiler.cell_estimate(directory/'design.json','warp_top'),
                tools=compiler.tool_versions(),physical_acceptance=False,timing_acceptance=False,
                scope='Oversized generated resource model only; placeholder routing timing, no equal-area or loaded-design claim')
    (directory/'case.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')


def main(model,out):
    if os.environ.get('GITHUB_ACTIONS')!='true':raise RuntimeError('Hosted only')
    model,out=Path(model).resolve(),Path(out).resolve()
    description=json.loads((model/'resource-control.json').read_text())
    if description['passed'] is not True or description['physical_candidate'] is not False:
        raise ValueError('Invalid resource control admission')
    import hashlib
    def hashes():return {name:hashlib.sha256((model/name).read_bytes()).hexdigest() for name in description['generated_sha256']}
    before=hashes()
    if before!=description['generated_sha256']:raise ValueError('Resource model changed')
    versions=compiler.tool_versions()
    if ('Yosys 0.66+179' not in versions['yosys'] or 'e74db6dea' not in versions['yosys']
            or 'nextpnr-0.11.1-34-gc4fbb55a' not in versions['nextpnr-generic']):
        raise ValueError('Unpinned compiler tools')
    out.mkdir(parents=True,exist_ok=False)
    result=dict(passed=False,cases={},model_input_sha256=before,tools=versions,
                run=os.environ.get('GITHUB_RUN_ID'),attempt=os.environ.get('GITHUB_RUN_ATTEMPT'),
                source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                physical_acceptance=False,timing_acceptance=False,equal_area_comparison=False)
    (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    try:
        for case in CASES:
            try:
                run_bounded([sys.executable,str(Path(__file__).resolve()),'--worker',case,str(model),str(out/case)],out/(case+'.log'))
                row=json.loads((out/case/'case.json').read_text())
                if row['case']!=case or row['tools']!=versions:raise ValueError('Worker identity differs')
                result['cases'][case]=row
            except Exception as exc:
                result['cases'][case]=failure_record(case,out/case,exc)
            (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
            print(json.dumps(dict(case=case,status=result['cases'][case].get('status','passed'),
                                  native_category=result['cases'][case].get('native_diagnosis',{}).get('category'))),flush=True)
        if hashes()!=before:raise ValueError('Model changed during compile')
        if any(row.get('status')=='failed' for row in result['cases'].values()):
            raise RuntimeError('One or more workload checks failed; all outcomes retained')
        result['passed']=True
    except Exception as exc:
        result['error']=str(exc)
        raise
    finally:
        (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')


def arguments(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',action='store_true')
    parser.add_argument('paths',nargs='+')
    args=parser.parse_args(argv)
    if len(args.paths)!=(3 if args.worker else 2):
        parser.error('Expected case/model/output for worker, or model/output for campaign')
    return args


if __name__=='__main__':
    args=arguments()
    if args.worker:worker(*args.paths)
    else:main(*args.paths)

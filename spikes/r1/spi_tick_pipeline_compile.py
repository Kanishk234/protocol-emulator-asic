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


def placement_seed(plan,case):
    seed=plan.get('candidate_seed',1)
    if type(seed) is not int or seed not in (1,2,3):raise ValueError('Unapproved bounded placement seed')
    if case not in ('control','candidate'):raise ValueError('Unknown compiler case')
    return 1 if case=='control' else seed


def prepare(capsule,proofs,out,candidate_seed=1,ungated_timer=False,known_inputs=False,candidate_min_ctrl=4,local_capture=False,uart_buffer=False,response_lane=False):
    from autonomy.check_xml import check_xml
    placement_seed({'candidate_seed':candidate_seed},'candidate')
    if type(known_inputs) is not bool:raise ValueError('Explicit Boolean input-routing mode required')
    if type(candidate_min_ctrl) is not int or candidate_min_ctrl not in (4,16):
        raise ValueError('Unapproved candidate control-sharing threshold')
    if type(local_capture) is not bool or local_capture and (not ungated_timer or not known_inputs or candidate_min_ctrl!=4):
        raise ValueError('Local capture requires the proved ungated/known-input source and original threshold')
    if (type(uart_buffer) is not bool or uart_buffer and
            (local_capture or not ungated_timer or not known_inputs or candidate_min_ctrl!=4)):
        raise ValueError('UART buffer is a separate proved-source experiment at the original threshold')
    if type(response_lane) is not bool or response_lane and not uart_buffer:
        raise ValueError('Response-lane placement requires the separate UART-buffer experiment')
    capsule,proofs,out=(Path(p).resolve() for p in (capsule,proofs,out))
    resource=capsule/'model/resource';desc=json.loads((resource/'resource-control.json').read_text())
    if desc['radix']!='radix8_2' or any(sha(resource/p)!=h for p,h in desc['generated_sha256'].items()):
        raise ValueError('Frozen R1 resource changed')
    source=ROOT/'protocols/spi_ctrl/spi_ctrl_top.v'
    if sha(source)!=SOURCE_SHA:raise ValueError('SPI source changed')
    candidate=variant(source.read_text(),ungated_timer=ungated_timer);seen=set();bound=[]
    import hashlib
    for folder in sorted(proofs.iterdir()):
        if not folder.is_dir():continue
        data=json.loads((folder/'result.json').read_text());identity=(data['mode'],data['half'])
        if identity in seen or not data['equivalence_passed'] or data['strict_source_tests']!=4:
            raise ValueError('Incomplete/duplicate SPI proof case')
        if data.get('ungated_timer',False) is not ungated_timer:
            raise ValueError('SPI proof uses a different timer enable variant')
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
    if known_inputs:bound.append(ROOT/'spikes/r1/known_lut_inputs.py')
    vendor=None
    if local_capture:
        from local_capture_controls import vendor_semantics
        vendor=Path.home()/'oss-cad-suite/share/yosys/fabulous/prims.v'
        vendor_semantics(vendor.read_text())
        bound += [ROOT/'spikes/r1/local_capture_controls.py',vendor]
    if uart_buffer:bound.append(ROOT/'spikes/r1/uart_input_buffer.py')
    if response_lane:bound.append(ROOT/'spikes/r1/response_lane_placement.py')
    (out/'plan.json').write_text(json.dumps(dict(capsule=str(capsule),resource=str(resource),arch=str(shadow),
        inputs={str(p):sha(p) for p in bound},params=report['params'],candidate_seed=candidate_seed,candidate_min_ctrl=candidate_min_ctrl,ungated_timer=ungated_timer,known_lut_inputs=known_inputs,local_capture=local_capture,vendor_cells=str(vendor) if vendor else None,uart_buffer=uart_buffer,response_lane=response_lane,
        scope=f'Source-proved registered SPI terminal pulse, timer enable '+('held high' if ungated_timer else 'state gated')+f', same frozen physical fabric, pins and parameters; original control seed1/MIN_CTRL4, candidate seed{candidate_seed}/MIN_CTRL{candidate_min_ctrl}, 50MHz request and GBUF USER-pinned to original bank D. '+('Candidate unused LUT inputs explicitly routed to existing reset with binary-equivalent truth tables. ' if known_inputs else '')+'Compiler timing remains uncharacterized; no native, extracted timing or adoption claim.'),indent=2)+'\n')


def run(out,case):
    from compile import compile as compiler
    from cloud_fresh_baseline import specification
    if os.environ.get('GITHUB_ACTIONS')!='true' or case not in ('control','candidate'):
        raise ValueError('Fresh compilation runs hosted with explicit cases')
    out=Path(out).resolve();plan=json.loads((out/'plan.json').read_text())
    seed=placement_seed(plan,case)
    threshold=plan.get('candidate_min_ctrl',4) if case=='candidate' else 4
    if type(threshold) is not int or threshold not in (4,16) or compiler.MIN_CTRL!=4:
        raise ValueError('Compiler control-sharing threshold differs from explicit plan/default')
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
    original=compiler.run;clock_constraint=None;input_transform=None;capture_transform=None;buffer_transform=None;response_transform=None
    def request_frequency(command,log,cwd,env=None):
        nonlocal clock_constraint,input_transform,capture_transform,buffer_transform,response_transform
        if Path(command[0]).name=='nextpnr-generic':
            command=[*command,'--freq','50']
            if case=='candidate':
                index=command.index('--json')+1;source=Path(command[index])
                if plan.get('uart_buffer',False):
                    from uart_input_buffer import buffer_uart_rx
                    derived,proof=buffer_uart_rx(json.loads(source.read_text()))
                    target=out/case/'design_uart_buffer.json';target.write_text(json.dumps(derived)+'\n')
                    receipt=out/case/'uart-buffer-proof.json';receipt.write_text(json.dumps(proof,indent=2)+'\n')
                    buffer_transform=dict(original_json_sha256=sha(source),derived_json_sha256=sha(target),
                        proof_sha256=sha(receipt),logical_buffer_luts=4,required_capture_bel='X6Y1/C',
                        expected_packed_capture_cell=proof['expected_packed_capture_cell'])
                    source=target
                if plan.get('response_lane',False):
                    from response_lane_placement import pin_response_lane
                    derived,proof=pin_response_lane(json.loads(source.read_text()))
                    target=out/case/'design_response_lane.json';target.write_text(json.dumps(derived)+'\n')
                    receipt=out/case/'response-lane-proof.json';receipt.write_text(json.dumps(proof,indent=2)+'\n')
                    response_transform=dict(original_json_sha256=sha(source),derived_json_sha256=sha(target),
                        proof_sha256=sha(receipt),retained_lut=proof['retained_lut'],required_bel=proof['required_bel'],
                        capture_output=proof['capture_output'],logical_graph_preserved=True)
                    source=target
                if plan.get('local_capture',False):
                    from local_capture_controls import vendor_semantics,absorb_capture
                    vendor=Path(compiler.tool('yosys')).parent.parent/'share/yosys/fabulous/prims.v'
                    if sha(vendor)!=sha(plan['vendor_cells']):raise ValueError('Used vendor cells differ from staged semantics')
                    vendor_semantics(vendor.read_text())
                    derived,proof=absorb_capture(json.loads(source.read_text()))
                    target=out/case/'design_local_capture.json';target.write_text(json.dumps(derived)+'\n')
                    receipt=out/case/'local-capture-proof.json';receipt.write_text(json.dumps(proof,indent=2)+'\n')
                    capture_transform=dict(original_json_sha256=sha(source),derived_json_sha256=sha(target),
                        proof_sha256=sha(receipt),changed_flip_flops=8,binary_transitions_per_ff=16,
                        same_ff_primitive_and_clock=True,vendor_cells_sha256=sha(vendor))
                    source=target
                if plan.get('known_lut_inputs',False):
                    from known_lut_inputs import fill_inputs
                    filled,proof=fill_inputs(json.loads(source.read_text()))
                    derived=out/case/'design_known_inputs.json';derived.write_text(json.dumps(filled)+'\n')
                    receipt=out/case/'known-input-proof.json';receipt.write_text(json.dumps(proof,indent=2)+'\n')
                    input_transform=dict(original_json_sha256=sha(source),derived_json_sha256=sha(derived),
                        proof_sha256=sha(receipt),changed_cells=proof['changed_cells'],reset_net=proof['reset_net'],
                        binary_cell_functions_preserved=True,sequential_and_hard_cells_preserved=True)
                    source=derived
                pinned,clock=pin_global_clock(json.loads(source.read_text()))
                target=out/case/'design_clock_d.json';target.write_text(json.dumps(pinned)+'\n')
                clock_constraint=dict(cell=clock,bel='X0Y4/D',logical_graph_preserved=True,
                    source_json_sha256=sha(source),pinned_json_sha256=sha(target))
                command[index]=str(target)
        return original(command,log,cwd,env)
    compiler.run=request_frequency;compiler.MIN_CTRL=threshold
    try:image,report=compiler.compile_design(sources,pins,Path(plan['arch']),out/case,seed=seed,set_params=params,strict_ports=True)
    finally:compiler.run=original;compiler.MIN_CTRL=4
    if report['build_options']['min_ctrl']!=threshold:
        raise ValueError('Reported control-sharing threshold differs from requested compile')
    if case=='control' and Path(image).read_bytes()!=(Path(plan['capsule'])/'model/compile/uart_spi_11/concurrency.wbit').read_bytes():
        raise ValueError('Original same-source compiler control image did not reproduce')
    if case=='candidate' and not (out/'control/result.json').is_file():raise ValueError('Original compile control missing')
    if case=='candidate':
        placed=json.loads((out/case/'design_pnr.json').read_text())['modules']['top']
        clocks=[c for c in placed['cells'].values() if c['type']=='GBUF']
        if clock_constraint is None or len(clocks)!=1 or clocks[0]['attributes']['NEXTPNR_BEL']!='X0Y4/D':
            raise ValueError('Candidate global clock constraint not honored')
        if plan.get('uart_buffer',False):
            cell=placed['cells'].get(buffer_transform['expected_packed_capture_cell'],{})
            if (cell.get('attributes',{}).get('NEXTPNR_BEL')!='X6Y1/C' or
                    int(cell.get('parameters',{}).get('FF','0'),2)!=1):
                raise ValueError('UART capture FF placement or registered mode not honored')
        if plan.get('response_lane',False):
            cell=placed['cells'].get(response_transform['retained_lut'],{})
            if (cell.get('attributes',{}).get('NEXTPNR_BEL')!=response_transform['required_bel'] or
                    int(cell.get('parameters',{}).get('FF','0'),2)!=1 or
                    cell.get('connections',{}).get('Q')!=placed['netnames']['u_user.r_lane']['bits']):
                raise ValueError('Response-lane retained LUT/FF placement not honored')
    words=BitFile.load(image)
    if words.arch_version!=0xfe or len(words.words)!=962:raise ValueError('Wrong diagnostic image format')
    (out/case/'result.json').write_text(json.dumps(dict(case=case,run=os.environ.get('GITHUB_RUN_ID'),source_sha=os.environ.get('GITHUB_SHA'),
        image_sha256=sha(image),placed_utilisation=report['utilisation'],model_fmax_mhz=report['fmax_mhz'],model_timing_characterized=False,
        requested_placement_frequency_mhz=50,yosys_version=version,nextpnr_version=np,
        clock_constraint=clock_constraint,placement_seed=seed,ungated_timer=plan.get('ungated_timer',False) if case=='candidate' else False,
        known_lut_inputs=plan.get('known_lut_inputs',False) if case=='candidate' else False,input_transform=input_transform,min_ctrl=threshold,
        local_capture=plan.get('local_capture',False) if case=='candidate' else False,capture_transform=capture_transform,
        uart_buffer=plan.get('uart_buffer',False) if case=='candidate' else False,buffer_transform=buffer_transform,
        response_lane=plan.get('response_lane',False) if case=='candidate' else False,response_transform=response_transform,
        actual_native_loading=False,timing_acceptance=False,physical_acceptance=False,adopted=False),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    x=sub.add_parser('prepare')
    for name in ('capsule','proofs','out'):x.add_argument('--'+name,type=Path,required=True)
    x.add_argument('--candidate-seed',type=int,choices=(1,2,3),default=1)
    x.add_argument('--ungated-timer',action='store_true')
    x.add_argument('--known-inputs',action='store_true')
    x.add_argument('--candidate-min-ctrl',type=int,choices=(4,16),default=4)
    x.add_argument('--local-capture',action='store_true')
    x.add_argument('--uart-buffer',action='store_true')
    x.add_argument('--response-lane',action='store_true')
    x=sub.add_parser('run');x.add_argument('--out',type=Path,required=True);x.add_argument('--case',choices=('control','candidate'),required=True)
    a=vars(p.parse_args());mode=a.pop('mode');(prepare if mode=='prepare' else run)(**a)

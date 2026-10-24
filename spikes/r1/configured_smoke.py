"""Load an audited compiler image through WARP's frame FSM, then test fabric I/O.

Diagnostic internal test; optional management SPI shell, no physical timing.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import subprocess
import shlex

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))

FULL_MAPPED_SHA={
'E_IO4':'3ddf61bd9cb82af25aeb8396daaa5bf42845ef3ce69aceddbeb1507e3d32e383',
'LUT4x8_ha':'b743335546eb7cbecd98d9fd129a26855e900ca4f868caea2f5a43167faf6b1a',
'NE_term':'9a665269d493de74a8791e5dc587f00ad0d22bd41bddfae04e1cf6cce6cb13e3',
'NW_term':'3f6acfbab923dc4161f741ad1b938978c601292bb1b079e0dc7846f5ccd4c094',
'N_IO':'f838036ef518e63b18590e410599381f328d0c6fe7b89cfd6e34ebefd22aca92',
'PRIM2T2S':'c1e0504142bf07a8b2a4bd15f3d931e8d01ddc09b71e6705083e5e58ba6134b1',
'SE_term':'18a40e0e2ca01d89713ef2feec952cc95fe0b60e5dc1887f9213ae0df9526bc1',
'SW_term':'a5306fbf62dc1ad6c8446b4cb24a9ff92311d03b86ee2a9973e423d9c8f6eb7c',
'S_IO2':'7790459362b2aba666c2e205888a96ceebafd290f303a83ba0c13a15ccfdc87c',
'W_IO4':'6dfe7498d1fc34d3012fa5e977f679ddbc6c72144a939a1aefb585b0a8df1a77'}
NATIVE_BALANCED_SHA={
'PRIM2T2S':'eae4727e546ab12e15978c780981a69b7d568222759d387f173ffbf5a0e28bf1',
'W_IO4':'979833b6a2d2b6c65067e5cd628f8812d0ab8525a52f00ab6445f7305ec620cc',
'NW_term':'9998abeb3819c42ba50ab841316e6109c088f3eaad546f875ff41342c08739b3',
'SW_term':'90a0f9a9a598ecdad2279324a85a9c200b45c6a04d2b0dd0ed44fddb88b7c0b2'}
NATIVE_COMPLETE_SHA={**NATIVE_BALANCED_SHA,
'E_IO4':'e715751729ff6894eb362738381b82a6d5dc6f089ad9a2ec57af7c7d50bf494e',
'LUT4x8_ha':'5d32817052df82d29993076e59ad4718e6c04b7d3ca86c461284681b2f3423a7',
'NE_term':'a3dcaff47a92d7aabc396114e6eaeae62c352565a274e5d1d83f17e01dfb842b',
'N_IO':'e74836a3c019e84d2cf723b886a3c47ce6d82666ef9ac45cf11b14f3e936eab6',
'SE_term':'69560dd40cd426096cc918ee149d55fa775d3c7173fca63c4fb52477b1927344',
'S_IO2':'e561271cac3864b2a9d5539347e15ce6ee7c18a59e5725ec6f8742581e85b41c'}


def drive_auxiliary_inputs(fabric_text,connections):
    ports=set(re.findall(r'\binput\s+(?:wire\s+)?(?:\[[^\]]+\]\s*)?(Tile_\w+)',fabric_text))
    reset='Tile_X0Y4_SYS_RESET_RESET_top'
    if reset not in ports:raise ValueError('Expected frozen fabric auxiliary reset input')
    connections[reset]='~rst_n'
    for port in ports:connections.setdefault(port,"1'b0")
    if any(not connections[p] for p in ports):raise ValueError('Undriven diagnostic fabric input')
    return sorted(ports)


def verify_input_hashes(expected):
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=digest for p,digest in expected.items()):
        raise ValueError('Simulation input changed during execution')


def complete_native_exports(audit_path):
    data=json.loads(Path(audit_path).read_text())
    if (data.get('passed') is not True or data.get('leaf_contexts')!=26 or data.get('grid_instances')!=40 or
        data.get('wire_feedthroughs_with_guides')!=52 or data.get('source_runs')!=
        dict(baseline='40013513454',critical='40030916359',remaining='40033384495') or
        set(data.get('native_exports',{}))!=set(NATIVE_COMPLETE_SHA)):
        raise ValueError('Require complete independently audited native source coverage')
    exports={}
    for tile,expected in NATIVE_COMPLETE_SHA.items():
        row=data['native_exports'][tile];path=Path(row['path']).resolve()
        if row['sha256']!=expected or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise ValueError('Changed complete native export: '+tile)
        exports[tile]=path
    return exports


def balanced_native_exports(root,baseline):
    root,baseline=Path(root).resolve(),Path(baseline).resolve();exports={};records=[]
    cases={'west_io':('W_IO4','47_52','12.00'),'northwest':('NW_term','47_52','12.00'),
           'southwest':('SW_term','47_52','12.00'),'primitive1':('PRIM2T2S','164_64','30.24'),
           'primitive4':('PRIM2T2S','164_64','107.04')}
    for name,(tile,width,phase) in cases.items():
        folder=root/('r1-balanced-leaf-40030916359-'+name)/'native'
        record=folder/'result.json';data=json.loads(record.read_text());records.append(record)
        row=data['cases']['width'+width]
        if (not data['passed'] or data['run']!='40030916359' or data['attempt']!='1' or
            data['tile']!=tile or data['balanced_case']['name']!=name or not row['passed'] or
            row['power_phase']['center_um']!=phase or data['mapped_nl_sha256']!=FULL_MAPPED_SHA[tile] or
            data['input_manifest_sha256']!=hashlib.sha256((baseline/'manifest.json').read_bytes()).hexdigest()):
            raise ValueError('Unqualified balanced native source: '+name)
        if any(row['final_power_grid_violations'].values()) or any(c['total_overflow'] or c['max_h_overflow'] or c['max_v_overflow'] for c in row['congestion']):
            raise ValueError('Native physical gates did not pass')
        nl=folder/('width'+width)/'10-openroad-detailedplacement'/(tile+'.nl.v')
        if hashlib.sha256(nl.read_bytes()).hexdigest()!=NATIVE_BALANCED_SHA[tile]:raise ValueError('Changed native balanced netlist')
        exports[tile]=nl
    return exports,records


def run(model,case,out,mapped_lut=None,pdk=None,icarus_root=None,mapped_bundle=None,postphysical_primitive=None,postphysical_balanced=None,postphysical_complete=None,capture_configuration=False,management_shell=False,shell_restart_only=False,quiesce_unused=False,restart_probe=False):
    native_primitive=any(p is not None for p in (postphysical_primitive,postphysical_balanced,postphysical_complete))
    if native_primitive and mapped_bundle is None:raise ValueError('Postphysical overrides require all-mapped baseline')
    if sum(p is not None for p in (postphysical_primitive,postphysical_balanced,postphysical_complete))>1:raise ValueError('Choose one native export profile')
    if capture_configuration and postphysical_complete is None:raise ValueError('Configuration-state observation requires complete native profile')
    if shell_restart_only and not management_shell:raise ValueError('Restart diagnostic requires management shell')
    if restart_probe and management_shell:raise ValueError('Direct restart probe is separate from full shell test')
    native_records=[]
    from cocotb_tools.runner import get_runner
    from compile.bitfile import BitFile
    model,case,out=(Path(p).resolve() for p in (model,case,out))
    manifest=json.loads((model/'resource-control.json').read_text())
    for name,digest in manifest['generated_sha256'].items():
        if hashlib.sha256((model/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Changed generated model')
    report=json.loads((case/'report.json').read_text())
    params=report['params']
    if (params.get('CPOL')!=0 or params.get('CPHA')!=0 or
            params.get('UART_PRIMS')!=1 or params.get('SPI_PRIMS')!=1):
        raise ValueError('This diagnostic smoke uses hard-backed UART/SPI mode0')
    images=list(case.glob('*.wbit'))
    if len(images)!=1:raise ValueError('Missing or ambiguous compiled image')
    image=images[0];bits=BitFile.load(image)
    if bits.arch_version!=0xFE:raise ValueError('Require diagnostic image')
    if hashlib.sha256(image.read_bytes()).hexdigest()!=report['provenance']['bitfile_sha256']:
        raise ValueError('Changed compiler image')
    out.mkdir(parents=True,exist_ok=False)
    quiescence=None;quiescence_inputs=[]
    if quiesce_unused:
        from profiling.r1_quiesce import derive
        image,quiescence,quiescence_inputs=derive(model,case,image,out)
    signals={'clk':'clk','rst_n':'rst_n','FAB_IN0':'rx_i','FAB_IN1':'miso_i',
             'FAB_OUT0':'tx_o','FAB_OUT1':'sck_o','FAB_OUT2':'mosi_o','FAB_OUT3':'cs_n_o'}
    names=('h_wdata','h_wlast','h_wvalid','h_rready','h_rdata','h_rvalid','h_wready','h_attention','h_status')
    connection={}
    for row in csv.DictReader((model/'pins.csv').open()):
        signal=signals.get(row['pin'])
        if signal is None and row['pin'].split('[')[0] in names:signal=row['pin']
        coordinate,letter=row['bel'].split('/')
        suffix={'in':'OUT_top','inout':'OUT_top','clock':'OUT_top','out':'IN_top','out_en':'EN_top'}[row['direction']]
        connection[f'Tile_{coordinate}_{letter}_{suffix}']=signal or ("1'b0" if suffix=='OUT_top' else '')
    driven_inputs=drive_auxiliary_inputs((model/'fabric.v').read_text(),connection)
    source='''`timescale 1ns/1ps
`default_nettype none
module r1_tb;
reg clk, rst_n, cfg_rst_n, cfg_strobe, cfg_restart;
reg [31:0] cfg_word;
reg rx_i, miso_i, h_wlast, h_wvalid, h_rready;
reg [7:0] h_wdata;
wire tx_o,sck_o,mosi_o,cs_n_o,h_rvalid,h_wready,h_attention;
wire [7:0] h_rdata,h_status;
wire [159:0] frame_data,frame_strobe;
wp_fabric_cfg #(.ROWS(5),.COLS(8)) loader(
.clk(clk),.rst_n(cfg_rst_n),.word(cfg_word),.word_strobe(cfg_strobe),
.restart(cfg_restart),.frame_data(frame_data),.frame_strobe(frame_strobe));
eFPGA fabric(
'''
    items=[f'.{p}({s})' for p,s in sorted(connection.items())]
    items+=['.FrameData(frame_data)','.FrameStrobe(frame_strobe)']
    source+=',\n'.join(items)+');\nendmodule\n'
    if management_shell:
        from profiling.r1_shell_adapter import shell_wrapper
        source,driven_inputs=shell_wrapper(model)
    wrapper=out/'tb.v';wrapper.write_text(source)
    lib=model/'library'
    sources=[wrapper,model/'fabric.v',*sorted((model/'rtl').glob('*.v')),lib/'models_pack.v']
    sources += [lib/'primitives'/n/'fabulous'/(n+'.v') for n in ('FABULOUS_LC','IOBUF','GBUF','SYS_RESET')]
    sources += sorted((lib/'primitives/WARP/fabulous').glob('*.v'))
    sources += [ROOT/'src'/n for n in ('wp_fabric_cfg.v','wp_frame_select.v','fabric_gen/ConfigFSM.v','fabric_gen/Frame_Data_Reg.v')]
    if management_shell:
        sources += [ROOT/'src'/n for n in ('wp_shell.v','wp_sync.v','wp_spi_target.v','wp_crc32.v','wp_fifo.v')]
    mapped=mapped_lut is not None or mapped_bundle is not None
    if mapped:
        if mapped_lut is not None and mapped_bundle is not None:raise ValueError('Choose one mapped mode')
        if manifest.get('radix')!='radix8_2':raise ValueError('Require frozen reduced-radix model')
        pdk=Path(pdk).resolve()
        if mapped_bundle is not None:
            mapped_bundle=Path(mapped_bundle).resolve()
            replacements={t:mapped_bundle/t/'tile.nl.v' for t in FULL_MAPPED_SHA}
        else:
            replacements={'LUT4x8_ha':Path(mapped_lut).resolve()}
        if any(hashlib.sha256(path.read_bytes()).hexdigest()!=FULL_MAPPED_SHA[t] for t,path in replacements.items()):
            raise ValueError('Require exact audited mapped tile netlist exports')
        if postphysical_primitive is not None:
            if mapped_bundle is None:raise ValueError('Native primitive override requires all-mapped baseline')
            native=Path(postphysical_primitive).resolve()
            if hashlib.sha256(native.read_bytes()).hexdigest()!='eae4727e546ab12e15978c780981a69b7d568222759d387f173ffbf5a0e28bf1':
                raise ValueError('Require exact successful40027428283native primitive export')
            replacements['PRIM2T2S']=native
        if postphysical_balanced is not None:
            native_exports,native_records=balanced_native_exports(postphysical_balanced,mapped_bundle)
            replacements.update(native_exports)
        if postphysical_complete is not None:
            replacements.update(complete_native_exports(postphysical_complete))
            native_records=[Path(postphysical_complete).resolve()]
        sources=[p for p in sources if p not in {model/'rtl'/(t+'.v') for t in replacements}]
        sources.extend(replacements.values())
        revision='2bbec755dc67ca3db0261c3d6163e15735d66710'
        for name in ('sg13cmos5l_stdcell.v','sg13cmos5l_udp.v'):
            path=pdk/'libs.ref/sg13cmos5l_stdcell/verilog'/name
            expected=subprocess.check_output(['git','-C',str(pdk.parent),'show',
                revision+':ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/verilog/'+name])
            if path.read_bytes()!=expected:raise ValueError('Modified PDK cell simulation model')
            sources.append(path)
        icarus_root=Path(icarus_root or Path.home()/'.cache/warp/iverilog-13').resolve()
        tools=out/'icarus-bin';tools.mkdir()
        for name,option in (('iverilog','-B'),('vvp','-M')):
            binary=icarus_root/'usr/bin'/name
            if not binary.is_file():raise ValueError('Mapped cell models require pinned Icarus13')
            wrapper=tools/name
            wrapper.write_text('#!/bin/sh\nexec '+shlex.quote(str(binary))+' '+option+' '+
                               shlex.quote(str(icarus_root/'usr/lib/ivl'))+' "$@"\n')
            wrapper.chmod(0o755)
        os.environ['PATH']=str(tools)+os.pathsep+os.environ['PATH']
        os.environ['IVERILOG_VPI_MODULE_PATH']=str(icarus_root/'usr/lib/ivl')
        version=subprocess.run(['iverilog','-V'],capture_output=True,text=True,check=True).stdout
        if 'version 13.0' not in version:raise ValueError('Mapped PDK models require Icarus13')
    provenance=[*sources,Path(__file__),ROOT/'test_internal/r1_configured/test_loaded.py',image,
                model/'resource-control.json',case/'report.json',*native_records,*quiescence_inputs]
    if quiesce_unused:provenance.append(out/'quiescence.json')
    if management_shell:
        from profiling import r1_shell_adapter
        provenance += [Path(r1_shell_adapter.__file__),ROOT/'test_internal/r1_configured/test_shell.py',
                       ROOT/'test/warp_host.py',ROOT/'tools/host/protocol.py']
    input_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in provenance}
    runner=get_runner('icarus')
    runner.build(sources=sources,hdl_toplevel='r1_tb',build_dir=out/'sim',build_args=['-g2012'],always=True)
    extra_env={'R1_IMAGE':str(image),'R1_DIV':str(params['DIV']),'R1_HALF':str(params['HALF'])}
    extra_env['R1_ACTIVITY']=str(out/'activity.json')
    extra_env['R1_SHELL_RESTART_ONLY']='1' if shell_restart_only else '0'
    extra_env['R1_RESTART_PROBE']='1' if restart_probe else '0'
    if capture_configuration:extra_env['R1_CFG_SNAPSHOT']=str(out/'configuration-state.json')
    runner.test(hdl_toplevel='r1_tb',test_module='test_shell' if management_shell else 'test_loaded',test_dir=ROOT/'test_internal/r1_configured',
                results_xml=str(out/'results.xml'),extra_env=extra_env,test_args=['-v'])
    from autonomy.check_xml import check_xml
    tests=check_xml(out/'results.xml',1)
    verify_input_hashes(input_hashes)
    activity=json.loads((out/'activity.json').read_text())
    if set(activity['windows_ns'])!={'uart_tx','uart_rx','spi'}:
        raise ValueError('Incomplete concurrent activity observation')
    windows=list(activity['windows_ns'].values())
    overlap=min(end for start,end in windows)-max(start for start,end in windows)
    if any(end<=start for start,end in windows) or overlap<=0 or activity['overlap_ns']!=overlap:
        raise ValueError('Primary activity does not overlap')
    snapshot=None
    if capture_configuration:
        captured=json.loads((out/'configuration-state.json').read_text())['tiles']
        baseline=json.loads((mapped_bundle/'manifest.json').read_text())
        expected=json.loads((mapped_bundle/'connections.json').read_text())['modules']['eFPGA']['cells']
        if set(captured)-set(expected):raise ValueError('Unknown observed fabric tile')
        count=0
        for name,cell in expected.items():
            required=baseline['tiles'][cell['type']]['configuration_latches']
            row=captured.get(name,dict(tile_type=cell['type'],q={}))
            if row['tile_type']!=cell['type'] or len(row['q'])!=required:
                raise ValueError('Native configuration observation census differs: '+name)
            if any(value not in ('0','1') for value in row['q'].values()):
                raise ValueError('Unresolved native configuration state: '+name)
            count+=len(row['q'])
        if count!=8736:raise ValueError('Incomplete native configuration-state observation')
        snapshot=dict(configuration_latches=count,sha256=hashlib.sha256((out/'configuration-state.json').read_bytes()).hexdigest(),
                      scope='Observed Q states after real frame loading for this primary image; not an independent expected-bit comparison or timing acceptance.')
    for name,digest in manifest['generated_sha256'].items():
        if hashlib.sha256((model/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Model changed during configured simulation')
    result=dict(passed=True,strict_tests=len(tests),params=params,
                input_sha256=input_hashes,
                model_manifest_sha256=hashlib.sha256((model/'resource-control.json').read_bytes()).hexdigest(),
                simulator=subprocess.run(['iverilog','-V'],capture_output=True,text=True,check=True).stdout.splitlines()[0],
                tool_binary_sha256=({name:hashlib.sha256((icarus_root/'usr/bin'/name).read_bytes()).hexdigest()
                                     for name in ('iverilog','vvp')} if mapped else {}),
                run=os.environ.get('GITHUB_RUN_ID'),attempt=os.environ.get('GITHUB_RUN_ATTEMPT'),
                source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                physical_acceptance=False,timing_acceptance=False,management_spi_shell_tested=management_shell,
                management_reload_tested=management_shell and not shell_restart_only,
                quiescence=quiescence,user_restart_probe_tested=restart_probe,
                driven_scalar_tile_inputs=len(driven_inputs),auxiliary_system_reset_driven=True,
                configuration_snapshot=snapshot,
                concurrent_activity=activity,
                mapped_lut_tiles_tested=16 if mapped else 0,
                mapped_primitive_tiles_tested=2 if mapped_bundle is not None else 0,
                mapped_tile_instances_tested=40 if mapped_bundle is not None else (16 if mapped else 0),
                postphysical_primitive_tiles_tested=2 if native_primitive else 0,
                postphysical_west_tile_instances_tested=5 if postphysical_balanced is not None or postphysical_complete is not None else 0,
                postphysical_tile_instances_tested=40 if postphysical_complete is not None else (7 if postphysical_balanced is not None else (2 if postphysical_primitive is not None else 0)),
                postphysical_placed_instances_tested=39 if postphysical_complete is not None else (7 if postphysical_balanced is not None else (2 if postphysical_primitive is not None else 0)),
                postphysical_wire_only_instances_tested=1 if postphysical_complete is not None else 0,
                postphysical_source_run='40030916359+40033384495' if postphysical_complete is not None else ('40030916359' if postphysical_balanced is not None else ('40027428283' if postphysical_primitive is not None else None)),
                scope=('All40leaf instances use audited native exports:39placed/output-buffered and1cell-free routed wire tile. Generated RTL interconnect and RTL frame FSM load the primary UART TX/RX plus SPI0/backpressure sample. No management SPI shell, detailed route, SDF/extracted/configured timing, physical macro assembly or whole-chip acceptance.'
                       if postphysical_complete is not None else
                       'Configured fabric uses exact native40030916359output-buffered/placed exports in7instances (2primitive/5west) and mapped baseline in33others. Real frame-FSM loading and UART TX/RX plus SPI0/backpressure; no management SPI shell, extracted/SDF timing, detailed route or whole-chip acceptance.'
                       if postphysical_balanced is not None else
                       'Configured fabric with both primitive instances using the exact native40027428283output-buffered/placed export; all other tiles mapped baseline. Real frame-FSM loading and UART TX/RX plus SPI0/backpressure; no management SPI shell, extracted/SDF timing, detailed route or whole-chip acceptance.'
                       if postphysical_primitive is not None else
                       'Configured fabric with all40tile instances mapped, real frame-FSM loading, UART TX/RX plus SPI0/backpressure. No management SPI shell, extracted/SDF timing, post-route or whole-chip acceptance.'
                       if mapped_bundle is not None else
                       'Configured fabric with mapped LUT tiles and RTL other tiles; no extracted timing, management SPI shell or whole-fabric gate-level acceptance.'
                       if mapped_lut is not None else
                       'Configured generated RTL UART TX/RX plus SPI mode0 and response backpressure, loading through WARP frame FSM. No management SPI shell or physical timing test.'))
    if management_shell:
        implementation=('Native leaf exports with RTL interconnect' if postphysical_complete is not None else
                        'Bare mapped leaf exports with RTL interconnect' if mapped_bundle is not None else
                        'Mixed mapped/generated RTL fabric' if mapped else 'Generated RTL fabric')
        result['scope']='Diagnostic management SPI load/CRC/architecture rejection, RUN/STOP/reload, synchronized inputs and registered/parked outputs with the primary UART/SPI image. '+implementation+' and production RTL shell. No detailed route, SDF, extracted timing or assembled physical macro acceptance.'
        if shell_restart_only:result['scope']='Restart-only diagnostic: '+result['scope'].replace('RUN/STOP/reload','RUN/STOP/restart without second image load')
    (out/'configured-smoke.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('model','case','out'):parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--mapped-lut',type=Path);parser.add_argument('--pdk',type=Path)
    parser.add_argument('--mapped-bundle',type=Path)
    parser.add_argument('--postphysical-primitive',type=Path)
    parser.add_argument('--postphysical-balanced',type=Path)
    parser.add_argument('--postphysical-complete',type=Path)
    parser.add_argument('--capture-configuration',action='store_true')
    parser.add_argument('--management-shell',action='store_true')
    parser.add_argument('--shell-restart-only',action='store_true',help='Diagnostic control omitting second image load; does not pass the reload gate')
    parser.add_argument('--quiesce-unused',action='store_true',help='Ground only unrouted outputs with an existing padded GND selection')
    parser.add_argument('--restart-probe',action='store_true',help='Check configured user reset and a second SPI transfer in direct-frame mode')
    parser.add_argument('--icarus-root',type=Path)
    a=parser.parse_args()
    if a.mapped_lut is not None and a.mapped_bundle is not None:parser.error('Choose one mapped mode')
    if (a.mapped_lut is not None or a.mapped_bundle is not None)!=(a.pdk is not None):parser.error('Mapped tiles require pinned PDK directory')
    if a.postphysical_primitive is not None and a.mapped_bundle is None:parser.error('Postphysical primitive requires all-mapped baseline')
    if a.postphysical_balanced is not None and (a.mapped_bundle is None or a.postphysical_primitive is not None):parser.error('Balanced native profile requires all-mapped baseline and cannot mix native profiles')
    if a.postphysical_complete is not None and (a.mapped_bundle is None or a.postphysical_primitive is not None or a.postphysical_balanced is not None):parser.error('Complete native profile requires all-mapped baseline and cannot mix native profiles')
    if a.capture_configuration and a.postphysical_complete is None:parser.error('Configuration observation requires complete native profile')
    run(a.model,a.case,a.out,a.mapped_lut,a.pdk,a.icarus_root,a.mapped_bundle,a.postphysical_primitive,a.postphysical_balanced,a.postphysical_complete,a.capture_configuration,a.management_shell,a.shell_restart_only,a.quiesce_unused,a.restart_probe)

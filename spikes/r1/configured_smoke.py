"""Load an audited compiler image through WARP's frame FSM, then test fabric I/O.

Diagnostic internal test; excludes management SPI shell and physical timing.
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

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))


def run(model,case,out):
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
    ports=re.findall(r'\binput\s+(Tile_\w+_OUT_top)',(model/'fabric.v').read_text())
    for port in ports:connection.setdefault(port,"1'b0")
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
    wrapper=out/'tb.v';wrapper.write_text(source)
    lib=model/'library'
    sources=[wrapper,model/'fabric.v',*sorted((model/'rtl').glob('*.v')),lib/'models_pack.v']
    sources += [lib/'primitives'/n/'fabulous'/(n+'.v') for n in ('FABULOUS_LC','IOBUF','GBUF','SYS_RESET')]
    sources += sorted((lib/'primitives/WARP/fabulous').glob('*.v'))
    sources += [ROOT/'src'/n for n in ('wp_fabric_cfg.v','wp_frame_select.v','fabric_gen/ConfigFSM.v','fabric_gen/Frame_Data_Reg.v')]
    runner=get_runner('icarus')
    runner.build(sources=sources,hdl_toplevel='r1_tb',build_dir=out/'sim',build_args=['-g2012'],always=True)
    runner.test(hdl_toplevel='r1_tb',test_module='test_loaded',test_dir=ROOT/'test_internal/r1_configured',
                results_xml=str(out/'results.xml'),extra_env={'R1_IMAGE':str(image),'R1_DIV':str(params['DIV']),
                                                            'R1_HALF':str(params['HALF'])})
    from autonomy.check_xml import check_xml
    tests=check_xml(out/'results.xml',1)
    for name,digest in manifest['generated_sha256'].items():
        if hashlib.sha256((model/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Model changed during configured simulation')
    provenance=[*sources,Path(__file__),ROOT/'test_internal/r1_configured/test_loaded.py',image]
    result=dict(passed=True,strict_tests=len(tests),params=params,
                input_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in provenance},
                model_manifest_sha256=hashlib.sha256((model/'resource-control.json').read_bytes()).hexdigest(),
                simulator=subprocess.run(['iverilog','-V'],capture_output=True,text=True,check=True).stdout.splitlines()[0],
                run=os.environ.get('GITHUB_RUN_ID'),attempt=os.environ.get('GITHUB_RUN_ATTEMPT'),
                source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                physical_acceptance=False,timing_acceptance=False,management_spi_shell_tested=False,
                scope='Configured generated RTL UART TX/RX plus SPI mode0 and response backpressure, loading through WARP frame FSM. No management SPI shell or physical timing test.')
    (out/'configured-smoke.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('model','case','out'):parser.add_argument('--'+key,type=Path,required=True)
    a=parser.parse_args();run(a.model,a.case,a.out)

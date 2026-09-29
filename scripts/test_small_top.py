"""Run the real TT cocotb test without requiring GNU make on the local host."""
from pathlib import Path
from cocotb_tools.runner import get_runner
import yaml
import os
import xml.etree.ElementTree as ET
import argparse
import hashlib
import json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--netlist', type=Path, help='Run the same pin test on an existing netlist, without SDF')
args = parser.parse_args()

root = Path(__file__).resolve().parents[1]
sources = yaml.safe_load((root/'info.yaml').read_text())['project']['source_files']
tools = root/'build/small-top-tools'
tools.mkdir(exist_ok=True)
iv = Path.home()/'.cache/warp/iverilog-13/usr'
wrapper = tools/'iverilog'
wrapper.write_text(f'#!/bin/sh\nexec "{iv}/bin/iverilog" -B "{iv}/lib/ivl" "$@"\n')
wrapper.chmod(0o755)
vvp = tools/'vvp'
if not vvp.exists():
    vvp.symlink_to(iv/'bin/vvp')
os.environ['PATH'] = str(tools)+':'+os.environ['PATH']
runner = get_runner('icarus')
mode = 'gl' if args.netlist else 'rtl'
inputs = [root/'src'/f for f in sources]
if args.netlist:
    pdk = Path.home()/'.cache/warp/pdk-2bbec755dc67ca3db0261c3d6163e15735d66710/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/verilog'
    inputs = [pdk/'sg13cmos5l_udp.v', pdk/'sg13cmos5l_stdcell.v', args.netlist.resolve()]
inputs += [root/'test/tb.v']
out = root/'build'/('small-top-'+mode)
out.mkdir(exist_ok=True)
manifest = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs+[root/'test/test.py',root/'test/small_counter_image.py']}
(out/'inputs.json').write_text(json.dumps(manifest,indent=2)+'\n')
results = out/'results.xml'
if results.exists():
    results.unlink()  # Never accept an old successful run after simulator failure.
runner.build(sources=inputs,
             hdl_toplevel='tb', build_dir=out/'sim', always=True)
runner.test(hdl_toplevel='tb', test_module='test', test_dir=root/'test',
            results_xml=results)
tree = ET.parse(results)
assert list(tree.iter('testcase')) and not list(tree.iter('failure'))

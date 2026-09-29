"""Run the real TT cocotb test without requiring GNU make on the local host."""
from pathlib import Path
from cocotb_tools.runner import get_runner
import yaml
import os
import xml.etree.ElementTree as ET

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
runner.build(sources=[root/'src'/f for f in sources]+[root/'test/tb.v'],
             hdl_toplevel='tb', build_dir=root/'build/small-top-sim', always=True)
runner.test(hdl_toplevel='tb', test_module='test', test_dir=root/'test',
            results_xml=root/'build/small-top-results.xml')
tree = ET.parse(root/'build/small-top-results.xml')
assert list(tree.iter('testcase')) and not list(tree.iter('failure'))

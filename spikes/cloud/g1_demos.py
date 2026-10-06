#!/usr/bin/env python3
"""Compile/audit four G1 demos and load each through the real RTL chip ports."""
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
env = dict(os.environ, PYTHONPATH=str(ROOT/'tools')+os.pathsep+str(ROOT/'test'))
out = ROOT/'build/cloud_g1_demos'
out.mkdir(exist_ok=False, parents=True)
cases = [
    ('monitor', 'uart_monitor', 'uart_monitor_top.v', 'demo', 'test_uart_monitor', 'WARP_UART_MONITOR_BITFILE', 0),
    ('fault', 'uart_monitor', 'uart_fault_monitor_top.v', 'fault', 'test_uart_fault_monitor', 'WARP_UART_FAULT_BITFILE', 0),
    ('capture', 'uart_capture', 'uart_capture_top.v', 'demo', 'test_uart_capture', 'WARP_UART_CAPTURE_BITFILE', 0),
    ('prescaled', 'uart_capture', 'uart_capture_top.v', 'prescaled', 'test_uart_capture', 'WARP_UART_CAPTURE_BITFILE', 2),
]
for name, directory, source, pins, module, variable, shift in cases:
    build = out/name
    cmd = [sys.executable, '-m', 'compile.compile',
           str(ROOT/f'protocols/{directory}/{source}'),
           *map(str, sorted((ROOT/'protocols/uart').glob('*.v'))),
           '--pins', str(ROOT/f'protocols/{directory}/{pins}.yaml'),
           '--arch', str(ROOT/'arch/warp_g1'), '--strict-ports', '-o', str(build)]
    with (out/f'{name}_compile.log').open('w') as log:
        subprocess.run(cmd, cwd=ROOT, env=env, check=True, stdout=log, stderr=subprocess.STDOUT)
    subprocess.run([sys.executable, '-m', 'compile.audit', str(build/'report.json')],
                   cwd=ROOT, env=env, check=True)
    image = build/f'{pins}.wbit'
    case_env = dict(env, **{variable: str(image), 'WARP_UART_CAPTURE_STAMP_SHIFT': str(shift),
                           'PWD': str(ROOT/'test')})
    result = out/f'{name}_rtl_results.xml'
    with (out/f'{name}_rtl.log').open('w') as log:
        subprocess.run(['make', '-C', str(ROOT/'test'), 'WARP_FABRIC=rtl',
                        f'COCOTB_TEST_MODULES={module}', f'SIM_BUILD={out/name}_sim',
                        f'COCOTB_RESULTS_FILE={result}'], cwd=ROOT/'test', env=case_env,
                       check=True, stdout=log, stderr=subprocess.STDOUT)
    xml = ET.parse(result).getroot()
    if len(xml.findall('.//testcase')) != 1 or any(xml.findall('.//'+tag)
                                                 for tag in ('failure','error','skipped')):
        raise RuntimeError(f'Loaded demo failed or skipped: {name}')
print('Four freshly compiled/audited real SPI-loaded G1 RTL demos passed')

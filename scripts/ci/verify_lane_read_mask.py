#!/usr/bin/env python3
"""Prove parallel lane register reads against the exact cached-selection source."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from verify_cached_port_select import verify as prepare_cached
from verify_cfg_staging import ROOT

BASE_HASH = '3d5bd1118faee6530513db2f87cc59bf859751694275a807421b4224b35ee7ed'
TRIAL_HASH = '5a2905a6c59ac4eb6efb621e95d5bd18d1b9f2dc1ad599f5c7690573760ffd06'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_delta(output):
    output = Path(output).resolve()
    source = output/'src/trw_lane.v'
    before = {p.name: digest(p) for p in (output/'src').iterdir() if p.is_file()}
    if before.get('trw_lane.v') != BASE_HASH:
        raise ValueError('Wrong lane read-mask base source')
    (output/'lane_read_gold.v').write_bytes(source.read_bytes())
    subprocess.run(['git', 'apply', str(ROOT/'spikes/r4_floorplan/lane_read_mask.patch')],
                   cwd=output, check=True)
    after = {p.name: digest(p) for p in (output/'src').iterdir() if p.is_file()}
    if after != {**before, 'trw_lane.v': TRIAL_HASH}:
        raise ValueError('Unexpected lane read-mask source changes')
    return source


def prove(output):
    output = Path(output).resolve()
    script = '''read_verilog -DSYNTHESIS -Isrc src/trw_alu.v lane_read_gold.v
hierarchy -top trw_lane
proc
flatten
memory
opt
rename trw_lane gold
design -stash gold
read_verilog -DSYNTHESIS -Isrc src/trw_alu.v src/trw_lane.v
hierarchy -top trw_lane
proc
flatten
memory
opt
rename trw_lane gate
design -stash gate
design -copy-from gold -as gold gold
design -copy-from gate -as gate gate
equiv_make gold gate equiv
hierarchy -top equiv
equiv_simple
equiv_induct -seq 2
equiv_status -assert
'''
    (output/'lane_read.ys').write_text(script)
    log_path = output/'lane_read_proof.log'
    with log_path.open('w') as log:
        subprocess.run(['yosys', '-Q', '-s', 'lane_read.ys'], cwd=output,
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
    match = re.search(r'Of those cells (\d+) are proven and 0 are unproven', log_path.read_text())
    if not match or 'Equivalence successfully proven!' not in log_path.read_text():
        raise ValueError('Missing complete lane read-mask equivalence evidence')
    return int(match[1])


def verify(output):
    output = Path(output).resolve()
    prepare_cached(output)
    source = apply_delta(output)
    receipt = dict(base_variant='bs-resync-cfg-tx-cached-select',
                   source_sha256=digest(source), equivalence_points=prove(output),
                   sram_address_bits=9, induction_sequence_cap=2,
                   physical_timing_proven=False,
                   source_hashes={p.name: digest(p) for p in (output/'src').glob('*.v')})
    (output/'lane_read_receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    print(json.dumps(verify(parser.parse_args().output), indent=2))

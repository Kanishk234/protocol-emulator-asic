#!/usr/bin/env python3
"""Prove the cached fabric selection delta against the exact verified TX base."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from verify_arithmetic_trial import verify as prepare_tx
from verify_cfg_staging import ROOT

BASE_HASH = '4aec82bef1bb97aada11be1ff75f7e4c3ac5fb8638271f2444453002f58c1506'
TRIAL_HASH = '1ffd8c8004d86ec93c7da8e2967650861e6f5d67b8e44e83bc977649298508ba'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def named_reference(original):
    # Name a combinational decode in the golden module so the sequential
    # proof can establish correspondence with the new cached state. Prove
    # this stateless reference transformation separately for every legal N.
    needle = '    // selected source; a sel beyond the list selects nothing'
    condition = "if ({28'd0, sel} == n) begin"
    if original.count(needle) != 1 or original.count(condition) != 1:
        raise ValueError('Wrong original source selection structure')
    decoder = '''    wire [N-1:0] select_mask;
    genvar sm;
    generate for (sm = 0; sm < N; sm = sm + 1) begin : g_select_mask
        assign select_mask[sm] = ({28'd0, sel} == sm);
    end endgenerate
'''
    return original.replace(needle, decoder+'\n'+needle).replace(condition, 'if (select_mask[n]) begin')


def prove(output, original, candidate, count, tag):
    script = f'''read_verilog -DSYNTHESIS -Isrc {original}
rename trw_chan_port gold
read_verilog -DSYNTHESIS -Isrc {candidate}
rename trw_chan_port gate
chparam -set N {count} gold gate
proc
memory
opt
equiv_make gold gate equiv
hierarchy -top equiv
equiv_simple
equiv_induct -seq 4
equiv_status -assert
'''
    (output/f'{tag}-n{count}.ys').write_text(script)
    log_path = output/f'{tag}-n{count}.log'
    with log_path.open('w') as log:
        subprocess.run(['yosys', '-Q', '-s', f'{tag}-n{count}.ys'], cwd=output,
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
    log = log_path.read_text()
    match = re.search(r'Of those cells (\d+) are proven and 0 are unproven', log)
    if not match or 'Equivalence successfully proven!' not in log:
        raise ValueError('Missing complete cached-selection proof')
    return int(match[1])


def verify(output):
    output = Path(output).resolve()
    prepare_tx('tx-late-cursor', output)
    source = output/'src/trw_chan_port.v'
    if digest(source) != BASE_HASH:
        raise ValueError('Wrong cached-selection base')
    original = source.read_text()
    (output/'original.v').write_text(original)
    (output/'gold.v').write_text(named_reference(original))
    before = {p.name: digest(p) for p in (output/'src').iterdir() if p.is_file()}
    subprocess.run(['git', 'apply', str(ROOT/'spikes/r4_floorplan/cached_port_select.patch')],
                   cwd=output, check=True)
    after = {p.name: digest(p) for p in (output/'src').iterdir() if p.is_file()}
    if after != {**before, 'trw_chan_port.v': TRIAL_HASH}:
        raise ValueError('Unexpected cached-selection source changes')
    receipt = dict(base='bs-resync-cfg-tx-cursor', source_sha256=TRIAL_HASH,
                   physical_timing_proven=False, proofs=[])
    for count in range(1, 17):
        alias = prove(output, 'original.v', 'gold.v', count, 'alias')
        cached = prove(output, 'gold.v', 'src/trw_chan_port.v', count, 'cached')
        receipt['proofs'].append(dict(sources=count, reference_points=alias, cached_points=cached))
    (output/'cached_select_receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.output), indent=2))

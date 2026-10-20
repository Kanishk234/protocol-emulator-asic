#!/usr/bin/env python3
"""Prepare and prove one arithmetic delta against the measured combined source."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from verify_cfg_staging import ROOT, prepare as prepare_combined

BASE_VARIANT = 'bs-resync-event-cfg-staging'
TRIALS = {
    'sample-csa': ('trw_pin_bs.v', 'sample_csa.patch',
        'c77f87ce20a8b2f7eec2b58b4db72476ccf4eb5fc89dde4d60b9461f486a346d',
        '16471aaa96a1c602aa1c5ac0091593998d0ae677d05c1ded0c254169a2a1c5fd'),
    'tx-late-cursor': ('trw_pin_tx.v', 'tx_late_cursor.patch',
        'f915736427f84e7a0f61052ae109b5e625f57bf93a2c988a09b480bcda980423',
        '29bdf26b9cf3d1939d8b8efe7833ac7d6ca1042c71e33c7065462f10e3c7951f'),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_delta(output, variant):
    """Fail before patching an unknown or mismatched source; verify all source files."""
    if variant not in TRIALS:
        raise ValueError('Unknown arithmetic trial')
    output = Path(output)
    name, patch, before, after = TRIALS[variant]
    source = output / 'src' / name
    snapshots = {p.name: digest(p) for p in (output / 'src').iterdir() if p.is_file()}
    if snapshots.get(name) != before:
        raise ValueError('Wrong measured arithmetic base source')
    (output / 'arithmetic_gold.v').write_bytes(source.read_bytes())
    subprocess.run(['git', 'apply', str(ROOT / 'spikes/r4_floorplan' / patch)],
                   cwd=output, check=True)
    expected = {**snapshots, name: after}
    actual = {p.name: digest(p) for p in (output / 'src').iterdir() if p.is_file()}
    if actual != expected:
        raise ValueError('Arithmetic delta changed unexpected source bytes')
    return source


def verify(variant, output):
    if variant not in TRIALS:
        raise ValueError('Unknown arithmetic trial')
    output = prepare_combined(output, BASE_VARIANT)
    source = apply_delta(output, variant)
    module = source.stem
    script = f'''read_verilog -DSYNTHESIS -Isrc arithmetic_gold.v
rename {module} gold
read_verilog -DSYNTHESIS -Isrc src/{source.name}
rename {module} gate
proc
memory
opt
equiv_make gold gate equiv
hierarchy -top equiv
equiv_simple
equiv_induct -seq 2
equiv_status -assert
'''
    (output / 'arithmetic.ys').write_text(script)
    with (output / 'arithmetic-proof.log').open('w') as log:
        subprocess.run(['yosys', '-Q', '-s', 'arithmetic.ys'], cwd=output,
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
    log = (output / 'arithmetic-proof.log').read_text()
    match = re.search(r'Of those cells (\d+) are proven and 0 are unproven', log)
    if not match or 'Equivalence successfully proven!' not in log:
        raise ValueError('Missing complete arithmetic equivalence evidence')
    receipt = dict(variant=variant, base_variant=BASE_VARIANT,
                   equivalence_points=int(match[1]), module=module,
                   source_sha256=digest(source), physical_timing_proven=False)
    (output / 'arithmetic_receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('variant', choices=TRIALS)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.variant, args.output), indent=2))

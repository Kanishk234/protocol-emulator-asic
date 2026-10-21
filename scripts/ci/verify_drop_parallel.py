"""Prove a stateless parallel counter delta against the exact lane-mask source."""
import argparse
import json
from pathlib import Path
import subprocess

from verify_cached_port_select import prove
from verify_cfg_staging import ROOT
from verify_lane_read_mask import digest, verify as prepare_lane_mask

BASE_HASH = '1ffd8c8004d86ec93c7da8e2967650861e6f5d67b8e44e83bc977649298508ba'
TRIAL_HASH = '16744944aba3d689112be8871a6defb228ded9c6c867442b646f25f7d87da657'


def apply_delta(output):
    output = Path(output).resolve()
    source = output/'src/trw_chan_port.v'
    before = {p.name: digest(p) for p in (output/'src').iterdir() if p.is_file()}
    if before.get('trw_chan_port.v') != BASE_HASH:
        raise ValueError('Wrong parallel counter source')
    (output/'drop_parallel_gold.v').write_bytes(source.read_bytes())
    subprocess.run(['git', 'apply', str(ROOT/'spikes/r4_floorplan/drop_parallel.patch')],
                   cwd=output, check=True)
    after = {p.name: digest(p) for p in (output/'src').iterdir() if p.is_file()}
    if after != {**before, 'trw_chan_port.v': TRIAL_HASH}:
        raise ValueError('Unexpected parallel counter source changes')
    return source


def verify(output):
    output = Path(output).resolve()
    prepare_lane_mask(output)
    source = apply_delta(output)
    proofs = [dict(sources=n, equivalence_points=prove(output, 'drop_parallel_gold.v',
              'src/trw_chan_port.v', n, 'drop-parallel')) for n in range(1, 17)]
    receipt = dict(base_variant='bs-resync-cfg-tx-cached-lane-mask',
                   source_sha256=digest(source), proofs=proofs,
                   induction_sequence_cap=4, new_state_bits=0,
                   physical_timing_proven=False,
                   source_hashes={p.name: digest(p) for p in (output/'src').glob('*.v')})
    (output/'drop_parallel_receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('output', type=Path)
    print(json.dumps(verify(p.parse_args().output), indent=2))

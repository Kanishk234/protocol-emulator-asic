"""Clean low-eight-bit configuration cache screen, with unchanged strict gates."""
import json
import os
from pathlib import Path

from native_drop_parallel_screen import run_screen
from verify_drop_parallel import TRIAL_HASH, digest
from verify_sample_delta_low8 import FIXTURE

VARIANT = 'bs-resync-cfg-tx-cached-lane-mask-drop-parallel-delta8'


def main():
    hashes = {f: h['after'] for f, h in json.loads(
        (FIXTURE / 'source_hashes.json').read_text()).items()}
    hashes.update({
        'trw_chan_port.v': TRIAL_HASH,
        'trw_pin_tx.v': '29bdf26b9cf3d1939d8b8efe7833ac7d6ca1042c71e33c7065462f10e3c7951f',
        'trw_lane.v': '5a2905a6c59ac4eb6efb621e95d5bd18d1b9f2dc1ad599f5c7690573760ffd06',
    })
    if os.environ.get('VARIANT') != VARIANT or any(
            digest(Path('src') / f) != h for f, h in hashes.items()):
        raise ValueError('Wrong verified low-eight-bit configuration-cache source')
    run_screen()


if __name__ == '__main__':
    main()

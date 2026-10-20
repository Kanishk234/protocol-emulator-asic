"""Seal four unseen R1 roles; do not print or inspect selected identities.

The entire pool is excluded from R1 training until freeze. This prevents the
coordinator's knowledge of the pool from authorizing profiling any member.
Selection uses SystemRandom; committed bytes and SHA256 bind the evaluation.
"""
import hashlib
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
POOL = {
    'ps2_host': 'Bidirectional host role, framed receive/parity and host transmit.',
    'jtag_controller': 'Host-commanded TAP traversal and variable-length serial shifts.',
    'i2s_receiver': 'Stereo serial receive, word boundaries and host delivery.',
    'manchester_transmitter': 'Host-fed bytes with programmable bit timing and framing.',
    'nec_ir_receiver': 'Pulse-timing frame decode and host event delivery.',
    'microwire_controller': 'Host-commanded half-duplex serial transfers and turnaround.'
}


def main():
    sealed = ROOT / 'docs/design/HELDOUT_R1_SEALED.json'
    manifest = ROOT / 'docs/design/HELDOUT_R1_MANIFEST.json'
    if sealed.exists() or manifest.exists():
        raise SystemExit('Refusing to replace an existing evaluation seal')
    names = sorted(random.SystemRandom().sample(list(POOL), 4))
    payload = dict(schema_version=1, status='sealed_until_R1_hardware_freeze',
                   selection_date='2026-10-20', count=4,
                   rules='No RTL/model implementation, profiling or architecture tuning on any pool member before R1 freeze. Research exact specifications and evaluate after freeze. Report nonfit without retuning.',
                   roles=[dict(name=name, scope=POOL[name]) for name in names])
    data = (json.dumps(payload, indent=2, sort_keys=True) + '\n').encode()
    with sealed.open('xb') as stream:
        stream.write(data)
    record = dict(schema_version=1, path=str(sealed.relative_to(ROOT)),
                  sha256=hashlib.sha256(data).hexdigest(), selected_count=4,
                  excluded_training_pool=sorted(POOL),
                  independence='Random selection hidden from tuning coordinator; all six pool roles excluded from training. No independent human/agent selection claimed.',
                  evaluation='After freeze, preserve existing pin/host budget and report fit, functionality, host servicing and timing scope. Any scope reduction must be reported, never silently substituted.')
    with manifest.open('x') as stream:
        json.dump(record, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print('Sealed four evaluation roles; SHA256 ' + record['sha256'])


if __name__ == '__main__':
    main()

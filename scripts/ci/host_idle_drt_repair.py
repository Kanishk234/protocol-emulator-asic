"""Bounded native repair of existing detailed wires; never signoff qualification."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path


def configure(config):
    if config.get('CLOCK_PERIOD') != 20:
        raise ValueError('Expected unchanged 20 ns source')
    result = deepcopy(config)
    result.update(OPENROAD_THREADS=4, DRT_OPT_ITERS=12,
                  DRT_SAVE_DRC_REPORT_ITERS=1, DRT_SAVE_SNAPSHOTS=False,
                  DRT_ANTENNA_REPAIR_ITERS=0)
    return result


def validate_source(root, manifest, run, artifact):
    root = Path(root).resolve()
    for key, actual in (('run', run), ('artifact', artifact)):
        if any(actual.get(k) != v for k, v in manifest[key].items()):
            raise ValueError('Wrong completed DRT diagnostic provenance')
    for name, expected in manifest['files'].items():
        path = root / name
        if not path.resolve().is_relative_to(root):
            raise ValueError('Source path escapes artifact root')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Changed DRT diagnostic evidence: ' + name)
    base = root / 'runs/host-idle-drt-diagnostic'
    receipt = json.loads((base / 'diagnostic_result.json').read_text())
    if (receipt.get('source_run') != 42394957445 or receipt.get('iteration_limit') != 42
            or receipt.get('reported_drc_errors') != 96):
        raise ValueError('Wrong bounded DRT source result')
    for key in ('physical_qualified', 'extracted_timing_performed',
                'post_route_antenna_qualified', 'official_gds_qualified'):
        if receipt.get(key) is not False:
            raise ValueError('Source diagnostic must not claim signoff qualification')
    step = base / '1-openroad-detailedrouting'
    state = json.loads((step / 'state_out.json').read_text())
    if state['metrics'].get('route__drc_errors') != 96:
        raise ValueError('Wrong source DRC metric')
    for key, suffix in (('odb', 'odb'), ('def', 'def'), ('nl', 'nl.v'),
                        ('pnl', 'pnl.v'), ('sdc', 'sdc')):
        expected = Path.cwd() / step.relative_to(root) / ('tt_um_tripwire.' + suffix)
        if Path(state[key]) != expected or not (step / expected.name).is_file():
            raise ValueError('Missing or foreign detailed-route view: ' + key)
    config = json.loads((step / 'config.json').read_text())
    if (config.get('CLOCK_PERIOD') != 20 or config.get('DRT_OPT_ITERS') != 42
            or config.get('DRT_ANTENNA_REPAIR_ITERS') != 0):
        raise ValueError('Wrong source diagnostic settings')
    # Do not carry inherited pre-route timing views into this routed experiment.
    state = deepcopy(state)
    for key in ('spef', 'sdf', 'lib'):
        state[key] = None
    return state

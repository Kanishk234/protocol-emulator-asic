"""Validate the exact completed clean C-selector route before extraction."""
import hashlib
import json
from pathlib import Path


def validate(root, manifest, run, artifact):
    root = Path(root).resolve()
    for key, actual in (('run', run), ('artifact', artifact)):
        assert all(actual.get(k) == v for k, v in manifest[key].items()), 'Wrong routed source provenance'
    for name, digest in manifest['files'].items():
        path = root / name
        assert not Path(name).is_absolute() and path.resolve().is_relative_to(root)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, 'Routed source hash mismatch: ' + name
    completion = json.loads((root / 'runs/c-select-pass-route/completion.json').read_text())
    require_completion(completion)
    assert completion['state'] == manifest['source_state']
    state = json.loads((root / manifest['source_state']).read_text())
    assert state['metrics'].get('route__drc_errors') == 0
    for key, suffix in (('odb','odb'),('def','def'),('nl','nl.v'),('pnl','pnl.v'),('sdc','sdc')):
        relative = Path(manifest['source_state']).parent / ('tt_um_tripwire.'+suffix)
        assert Path(state[key]) == Path.cwd()/relative, 'Wrong routed state view: '+key
        assert (root/relative).is_file(), 'Missing routed state view: '+key
    antenna = json.loads((root/manifest['antenna_metrics']).read_text())
    assert antenna.get('antenna__violating__nets') == 0 and antenna.get('antenna__violating__pins') == 0
    pins = json.loads((root/manifest['disconnected_metrics']).read_text())
    assert pins.get('design__critical_disconnected_pin__count') == 0
    assert pins.get('design__disconnected_pin__count') == manifest['noncritical_disconnected_pins']
    return root / manifest['source_state']


def require_completion(receipt):
    for key in ('detailed_routing_completed', 'disconnected_pin_checker_passed'):
        assert receipt.get(key) is True
    for key in ('route_drc_errors', 'antenna_violating_nets'):
        assert type(receipt.get(key)) is int and receipt[key] == 0
    assert receipt.get('source_run') == 42156980762
    assert receipt.get('extracted_timing_performed') is False
    assert receipt.get('official_gds_qualified') is False

"""Authenticate a successful route and replay its exact extracted-state netlist."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

from closure_route import digest, SOURCE_RUN, SOURCE_SHA, CONFIG_SHA, timing_gate
from event_nor2_screen import logical_cells
from postgrt_timing import CORNERS

ROUTE_RUN = 42693952530
ROUTE_SHA = 'ebf817e8554cc4bbeb3ebc764c7707115e66681c'
RUNNER_ROOT = PurePosixPath('/home/runner/work/protocol-emulator-asic/protocol-emulator-asic')
SCREEN_RECEIPT = Path(__file__).resolve().parents[2] / 'docs/reports/closure_screen_42681697462.json'


def source_context(run, artifact=None, *, completed=True):
    expected = dict(id=ROUTE_RUN, head_sha=ROUTE_SHA, head_branch='tripwire/closure-8x4',
                    path='.github/workflows/tripwire-closure-route.yaml', run_attempt=1)
    if completed: expected.update(status='completed', conclusion='success')
    if any(run.get(k) != v for k, v in expected.items()):
        raise ValueError('Wrong or unqualified route source')
    if artifact is not None:
        if (artifact.get('name') != f'tripwire-qualified-route-{ROUTE_RUN}'
                or artifact.get('expired') is not False
                or artifact.get('workflow_run', {}).get('id') != ROUTE_RUN
                or artifact.get('workflow_run', {}).get('head_sha') != ROUTE_SHA
                or not isinstance(artifact.get('digest'), str)
                or not artifact['digest'].startswith('sha256:') or len(artifact['digest']) != 71):
            raise ValueError('Wrong route artifact')


def member(path, prefix):
    p = PurePosixPath(path)
    if p.is_absolute(): p = p.relative_to(RUNNER_ROOT)
    prefixes = (prefix,) if isinstance(prefix, str) else prefix
    if '..' in p.parts or '\\' in str(p) or not any(str(p).startswith(item + '/') for item in prefixes):
        raise ValueError('Physical view outside the required route stage')
    return str(p)


def validate(run, artifact, archive, expected, output):
    source_context(run, artifact)
    if 'sha256:' + digest(archive) != artifact['digest']:
        raise ValueError('Routed archive digest mismatch')
    if output.exists(): raise ValueError('Refusing to overwrite prior replay evidence')
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        if len(names) != len(set(names)): raise ValueError('Duplicate archive members')
        def read(name): return json.loads(bundle.read(name))
        completion = read('runs/closure-route/completion.json')
        requirements = dict(source_run=SOURCE_RUN, source_sha=SOURCE_SHA,
            detailed_routing_completed=True, extracted_timing_passed=True,
            route_drc_errors=0, final_antenna_nets=0, final_antenna_pins=0,
            disconnected_pin_checker_passed=True, minimum_fast_hold_ns=0.05,
            official_gds_signoff=False, routed_protocol_replay_performed=False)
        if any(type(completion.get(k)) is not type(v) or completion[k] != v for k, v in requirements.items()):
            raise ValueError('Incomplete or failed route/extraction gates')
        views = {member(name, 'runs/stock-official-baseline'): sha
                 for name, sha in completion['source_views'].items()}
        known = json.loads(SCREEN_RECEIPT.read_text())['frozen_views']
        if views != {k: v for k, v in known.items() if k.startswith('runs/stock-official-baseline/')}:
            raise ValueError('Route did not preserve the authenticated source-view set')
        for key, sha in views.items():
            if hashlib.sha256(bundle.read(key)).hexdigest() != sha:
                raise ValueError('Frozen source view hash mismatch')
        if hashlib.sha256(bundle.read('src/config.json')).hexdigest() != CONFIG_SHA:
            raise ValueError('Foreign routed hardware recipe')
        for folder in ('src', 'macro'):
            local = {str(p.relative_to(expected)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in (expected / folder).rglob('*') if p.is_file() and p.suffix != '.json'}
            actual = {n: hashlib.sha256(bundle.read(n)).hexdigest() for n in names
                      if n.startswith(folder + '/') and not n.endswith(('/', '.json'))}
            if local != actual: raise ValueError('Route source differs from prepared candidate')
        if bundle.read('info.yaml') != (expected / 'info.yaml').read_bytes():
            raise ValueError('Route metadata differs')
        stages = {}
        for label, suffix in [('route', '-openroad-detailedrouting/state_out.json'),
                              ('extracted', '-openroad-stapostpnr/state_out.json')]:
            prefix = 'runs/closure-route/' if label == 'route' else 'runs/extracted-timing/'
            found = [n for n in names if n.startswith(prefix) and n.endswith(suffix)]
            if len(found) != 1: raise ValueError('Missing unique completed ' + label + ' state')
            stages[label] = read(found[0])
        if type(stages['route']['metrics'].get('route__drc_errors')) is not int or stages['route']['metrics']['route__drc_errors'] != 0:
            raise ValueError('Final native route DRC is not zero')
        nls = {label: member(state['nl'], 'runs/closure-route' if label == 'route' else
                            ('runs/closure-route', 'runs/extracted-timing'))
               for label, state in stages.items()}
        # Extraction may inherit the DRT netlist rather than export a new one.
        # Accept only those two exact pipeline stage scopes, never other views.
        route_data = bundle.read(nls['route'])
        data = bundle.read(nls['extracted'])
        if logical_cells(route_data.decode()) != logical_cells(data.decode()):
            raise ValueError('Extraction changed logical cells/connectivity')
        if b'module tt_um_tripwire' not in data or b'RM_IHPSG13_1P_512x16_c2_bm_bist' not in data:
            raise ValueError('Full-chip SRAM netlist missing')
        summary = read('runs/extracted-timing/corner_summary.json')
        electrical = read('runs/extracted-timing/electrical_summary.json')
        rows = {}
        for corner in CORNERS:
            row = dict(summary)
            for kind, key in [('slew', 'slew'), ('cap', 'capacitance'), ('fanout', 'fanout')]:
                row[f'design__max_{kind}_violation__count__corner:{corner}'] = electrical[corner]['counts'][key]
            rows[corner] = {'before': row, 'after': row}
        timing_gate({'corners': rows})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    receipt = dict(route_run=ROUTE_RUN, route_sha=ROUTE_SHA, artifact_id=artifact['id'],
        archive_sha256=artifact['digest'], netlist_member=nls['extracted'],
        netlist_sha256=hashlib.sha256(data).hexdigest(), final_route_sha256=hashlib.sha256(route_data).hexdigest(),
        exact_extracted_state_netlist=True, logical_cells_match_route=True,
        functional_simulation_only=True, sdf_annotated=False, official_gds_qualified=False)
    output.with_suffix('.identity.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt

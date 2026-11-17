"""Replay the measured diagnostic netlist without promoting its failed screen."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

from closure_route import CONFIG_SHA, digest
from closure_final_gl import member
from event_nor2_screen import logical_cells
from extracted_timing import check_stock_report_uncertainty
from postgrt_timing import CORNERS
from selector_drt_diagnostic import assess, context as screen_context, SOURCE_RUN, SOURCE_SHA
from selector_final_gl import prepare_expected, verify_expected, screen_views

ROUTE_RUN = 44025267292
ROUTE_SHA = '1ad120d0e0952fc6a404947f9304dce0d851e91c'
ARTIFACT_NAME = f'selector-drt-diagnostic-{ROUTE_RUN}'
PREFIX = 'runs/selector-drt-diagnostic'


def source_context(run, artifact=None, *, completed=True):
    expected = dict(id=ROUTE_RUN, head_sha=ROUTE_SHA, head_branch='tripwire/closure-8x4',
                    path='.github/workflows/tripwire-selector-drt-diagnostic.yaml', run_attempt=1)
    if completed:
        expected.update(status='completed', conclusion='success')
    if any(run.get(k) != v for k, v in expected.items()):
        raise ValueError('Wrong or unsuccessful measured diagnostic')
    if artifact is not None:
        value = artifact.get('digest', '')
        if (artifact.get('name') != ARTIFACT_NAME or artifact.get('expired') is not False
                or artifact.get('workflow_run', {}).get('id') != ROUTE_RUN
                or artifact.get('workflow_run', {}).get('head_sha') != ROUTE_SHA
                or not isinstance(value, str) or not value.startswith('sha256:')
                or len(value) != 71 or any(c not in '0123456789abcdef' for c in value[7:])):
            raise ValueError('Wrong measured diagnostic archive')


def validate(run, artifact, archive, expected, output, *, screen_run, screen_artifact, screen_archive):
    source_context(run, artifact)
    views = screen_views(screen_run, screen_artifact, screen_archive, admit=screen_context)
    verify_expected(expected)
    if 'sha256:' + digest(archive) != artifact['digest']:
        raise ValueError('Diagnostic archive digest mismatch')
    if output.exists():
        raise ValueError('Refusing to replace prior replay evidence')
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate diagnostic archive members')
        def read(name):
            return json.loads(bundle.read(name))
        def one(prefix, suffix):
            found = [n for n in names if n.startswith(prefix + '/') and n.endswith(suffix)]
            if len(found) != 1:
                raise ValueError('Missing unique diagnostic stage: ' + suffix)
            return found[0]
        result = read(PREFIX + '/diagnostic_result.json')
        required = dict(source_run=SOURCE_RUN, source_sha=SOURCE_SHA,
                        source_screen_qualified=False, release_qualified=False,
                        official_gds_qualified=False, hardware_promoted=False,
                        native_stock_constraints=True, clock_uncertainty_ns=0.25,
                        logical_connectivity_preserved=True,
                        final_measured_gates_passed=True, timing_and_electrical_passed=True,
                        failures=[])
        if any(type(result.get(k)) is not type(v) or result[k] != v for k, v in required.items()):
            raise ValueError('Missing passing measurements or altered diagnostic scope')
        actual_views = {member(p, 'runs/stock-official-baseline'): value
                        for p, value in result['source_views'].items()}
        if actual_views != views or any(hashlib.sha256(bundle.read(p)).hexdigest() != value
                                       for p, value in views.items()):
            raise ValueError('Original diagnostic views changed')
        if digest(expected / 'src/config.json') != CONFIG_SHA or hashlib.sha256(
                bundle.read('src/config.json')).hexdigest() != CONFIG_SHA:
            raise ValueError('Foreign diagnostic recipe')
        for folder in ('src', 'macro'):
            local = {str(p.relative_to(expected)): digest(p)
                     for p in (expected / folder).rglob('*') if p.is_file() and p.suffix != '.json'}
            actual = {n: hashlib.sha256(bundle.read(n)).hexdigest() for n in names
                      if n.startswith(folder + '/') and not n.endswith(('/', '.json'))}
            if actual != local:
                raise ValueError('Diagnostic hardware differs from expected source')
        if bundle.read('info.yaml') != (expected / 'info.yaml').read_bytes():
            raise ValueError('Diagnostic metadata changed')
        policy = read('runs/extracted-timing/constraint_identity.json')
        sdc = bundle.read(member(policy['sta_constraint_file'], 'runs/extracted-timing'))
        if (policy.get('policy') != 'stock-native-base-sdc'
                or policy.get('clock_uncertainty_ns') != 0.25
                or policy.get('legacy_source_sdc_used') is not False
                or sdc != b'source $::env(SCRIPTS_DIR)/base.sdc\n'
                or hashlib.sha256(sdc).hexdigest() != policy.get('sha256')):
            raise ValueError('Native stock constraints missing')
        route = read(one(PREFIX + '/route', '-openroad-detailedrouting/state_out.json'))
        if type(route['metrics'].get('route__drc_errors')) is not int or route['metrics']['route__drc_errors'] != 0:
            raise ValueError('Completed zero-DRC diagnostic required')
        connected = read(one(PREFIX + '/final-native-checks', '-checker-disconnectedpins/state_out.json'))
        count = connected['metrics'].get('design__critical_disconnected_pin__count')
        if type(count) is not int or count != 0:
            raise ValueError('Diagnostic has disconnected pins or missing connectivity measurement')
        antenna = read(one(PREFIX + '/final-native-checks', '-openroad-checkantennas/or_metrics_out.json'))
        timing = read('runs/extracted-timing/corner_summary.json')
        electrical = read('runs/extracted-timing/electrical_summary.json')
        if not assess(timing, electrical, antenna)['final_measured_gates_passed']:
            raise ValueError('Actual diagnostic measurements fail')
        if (timing != result['extracted_timing'] or electrical != result['extracted_electrical']
                or antenna != result['final_antenna']):
            raise ValueError('Diagnostic summary differs from fresh measurements')
        sta_member = one('runs/extracted-timing', '-openroad-stapostpnr/state_out.json')
        sta = read(sta_member)
        stage = str(PurePosixPath(sta_member).parent)
        for corner in CORNERS:
            for report in ('max.rpt', 'min.rpt'):
                check_stock_report_uncertainty(bundle.read(f'{stage}/{corner}/{report}').decode())
        route_nl = member(route['nl'], PREFIX + '/route')
        sta_nl = member(sta['nl'], (PREFIX + '/route', 'runs/extracted-timing'))
        route_data, data = bundle.read(route_nl), bundle.read(sta_nl)
        if logical_cells(route_data.decode()) != logical_cells(data.decode()):
            raise ValueError('Diagnostic extraction changed logical connectivity')
        if b'module tt_um_tripwire' not in data or b'RM_IHPSG13_1P_512x16_c2_bm_bist' not in data:
            raise ValueError('Full-chip SRAM netlist missing')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    receipt = dict(route_run=ROUTE_RUN, route_sha=ROUTE_SHA, artifact_id=artifact['id'],
                   archive_sha256=artifact['digest'], netlist_member=sta_nl,
                   netlist_sha256=hashlib.sha256(data).hexdigest(),
                   exact_extracted_state_netlist=True, logical_cells_match_route=True,
                   functional_simulation_only=True, sdf_annotated=False,
                   source_screen_qualified=False, release_qualified=False,
                   official_gds_qualified=False, hardware_promoted=False)
    output.with_suffix('.identity.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt

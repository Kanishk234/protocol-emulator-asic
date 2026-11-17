"""Bounded stock DRT measurement of one antenna-only failed screen.

This never emits a qualified-route completion receipt or promotes its source.
Normal release restoration/routing gates are not changed.
"""
import argparse
import json
import os
from pathlib import Path
import shutil

from closure_route import (CONFIG_SHA, IMAGE, IMAGE_DIGEST, PDK, TOOLS, digest,
                           unpack, inventory, one, saved_screen, bound_hashes, timing_gate)
from selector_route import (SOURCE_RUN, SOURCE_SHA, EXTRA_ROOTS, expected_source,
                            context as screen_context)
from postgrt_timing import CORNERS, screen

ARTIFACT_ID = 14273234160
ARCHIVE_SHA = 'sha256:c5960d08c37756288ffa5d1bcb5be240a2617a192f5a37c9f038c07fc85fba26'
DRT_SCRIPT_SHA = 'e7e4e4984dff976e96fdf42561b185000bc2a9a3a21553b9bc781cfaef94447f'
ANTENNA_FAILURES = ['antenna__violating__nets: 1', 'antenna__violating__pins: 1']


def context(run, artifact=None):
    screen_context(run, artifact, completed=False)
    if (run.get('status'), run.get('conclusion')) != ('completed', 'failure'):
        raise ValueError('Diagnostic needs the exact retained failed screen')
    if artifact is not None and (artifact.get('id') != ARTIFACT_ID or artifact.get('digest') != ARCHIVE_SHA):
        raise ValueError('Foreign diagnostic source archive')


def admit_failure(result):
    if (result.get('qualified') is not False or result.get('failures') != ANTENNA_FAILURES
            or type(result.get('final_global_overflow')) is not int
            or result.get('final_global_overflow') != 0):
        raise ValueError('Only the exact antenna-only failure is admitted for measurement')


def restore_source(root, frozen, expected):
    if inventory(frozen) != inventory(expected):
        raise ValueError('Diagnostic source differs from reconstructed selector RTL')
    if digest(frozen / 'src/config.json') != CONFIG_SHA:
        raise ValueError('Wrong diagnostic source recipe')
    if (frozen / 'info.yaml').read_bytes() != (expected / 'info.yaml').read_bytes():
        raise ValueError('Wrong diagnostic platform metadata')
    engine = json.loads((frozen / 'compatibility-engine.json').read_text())
    if any(engine.get(k) != v for k, v in dict(librelane='3.1.0.dev4', pdk_revision=PDK, tools_sha=TOOLS).items()):
        raise ValueError('Wrong source engine')
    images = json.loads((frozen / 'compatibility-image.json').read_text())
    if len(images) != 1 or IMAGE.rsplit(':', 1)[0] + '@' + IMAGE_DIGEST not in images[0]['RepoDigests']:
        raise ValueError('Wrong source image')
    if (root / 'runs').exists():
        raise ValueError('Diagnostic needs a fresh physical workspace')
    source = one(frozen / 'runs/stock-official-baseline', '*-openroad-stamidpnr-3/state_out.json')
    recorded = json.loads((frozen / 'runs/stock-corner-audit/read_only_audit.json').read_text())
    state_path = Path(recorded['source_state'])
    if not state_path.is_absolute():
        state_path = root / state_path
    if state_path.resolve() != (root / source.relative_to(frozen)).resolve():
        raise ValueError('Saved runner paths cannot be rewritten')
    config = json.loads((frozen / 'src/config_merged.json').read_text())
    if (config.get('CLOCK_PERIOD') != 20 or config.get('DIE_AREA') != '0 0 1724.16 710.64'
            or config.get('RT_MAX_LAYER') != 'Metal4'):
        raise ValueError('Wrong diagnostic platform')
    for folder in ('src', 'macro', 'runs'):
        shutil.copytree(frozen / folder, root / folder, dirs_exist_ok=folder != 'runs')
    shutil.copy2(frozen / 'info.yaml', root / 'info.yaml')
    result = saved_screen(root)
    admit_failure(result)
    signoff = json.loads((root / 'runs/stock-signoff-estimate/qualification.json').read_text())
    if signoff.get('qualified') is not True or signoff.get('failures') != []:
        raise ValueError('Other saved timing checks failed')
    source = root / source.relative_to(frozen)
    state = json.loads(source.read_text())
    paths = [source, root / 'src/signoff.sdc'] + [Path(state[k]) for k in ('odb', 'def', 'nl', 'pnl', 'sdc')]
    bound_hashes(root, signoff['unchanged_source_hashes'], paths)
    timing_gate(json.loads((root / 'runs/stock-signoff-estimate/comparison.json').read_text()))
    result.update(source_run=SOURCE_RUN, source_sha=SOURCE_SHA, diagnostic_only=True,
                  release_qualified=False, saved_state_rewritten=False)
    (root / 'runs/selector-diagnostic-source.json').write_text(json.dumps(result, indent=2) + '\n')
    return source


def assess(timing, electrical, antenna):
    rows = {}
    for corner in CORNERS:
        row = dict(timing)
        for kind, key in (('slew', 'slew'), ('cap', 'capacitance'), ('fanout', 'fanout')):
            row[f'design__max_{kind}_violation__count__corner:{corner}'] = electrical[corner]['counts'][key]
        rows[corner] = dict(before=row, after=row)
    failures = []
    try:
        timing_gate(dict(corners=rows))
    except ValueError as error:
        failures.append(str(error))
    timing_passed = not failures
    for key in ('antenna__violating__nets', 'antenna__violating__pins'):
        if type(antenna.get(key)) is not int or antenna[key] < 0:
            raise ValueError('Missing final native antenna measurement')
        if antenna[key]:
            failures.append(f'{key}: {antenna[key]}')
    return dict(timing_and_electrical_passed=timing_passed,
                final_measured_gates_passed=not failures, failures=failures,
                source_screen_qualified=False, release_qualified=False,
                official_gds_qualified=False, hardware_promoted=False)


def measure(root):
    from native_stock_route import run_step
    from sram_bank_clean_route import validate_final_route
    from extracted_timing import main as extract, route_checkpoint
    from event_nor2_screen import logical_cells
    receipt = json.loads((root / 'runs/selector-diagnostic-source.json').read_text())
    admit_failure(receipt)
    if ((receipt.get('source_run'), receipt.get('source_sha')) != (SOURCE_RUN, SOURCE_SHA)
            or receipt.get('diagnostic_only') is not True
            or receipt.get('release_qualified') is not False):
        raise ValueError('Wrong diagnostic source receipt')
    expected = Path(os.environ['CLOSURE_EXPECTED_SOURCE'])
    if inventory(root) != inventory(expected) or digest(root / 'src/config.json') != CONFIG_SHA:
        raise ValueError('Source changed before diagnostic')
    if (root / 'info.yaml').read_bytes() != (expected / 'info.yaml').read_bytes():
        raise ValueError('Metadata changed before diagnostic')
    initial = root / 'runs/closure-initialize'
    resolved = json.loads((initial / 'resolved.json').read_text())
    pdk = Path(resolved['PDK_ROOT'])
    if pdk.name != PDK or not (pdk / 'ihp-sg13cmos5l').is_dir():
        raise ValueError('Wrong Ciel diagnostic PDK')
    os.environ['PDK_ROOT'] = str(pdk)
    fresh = json.loads(one(initial, '*-openroad-checkantennas/or_metrics_out.json').read_text())
    if any(type(fresh.get(k)) is not int or fresh[k] != 1
           for k in ('antenna__violating__nets', 'antenna__violating__pins')):
        raise ValueError('Fresh original antenna control did not reproduce')
    source = one(root / 'runs/stock-official-baseline', '*-openroad-stamidpnr-3/state_out.json')
    state = json.loads(source.read_text())
    paths = [source] + [Path(state[k]) for k in ('odb', 'def', 'nl', 'pnl', 'sdc')]
    before = {str(p): digest(p) for p in paths}
    output = root / 'runs/selector-drt-diagnostic'
    output.mkdir(exist_ok=False)
    cfg = json.loads((root / 'src/config_merged.json').read_text())
    audit = output / 'fresh-stock-timing'
    screen(root / 'src/config_merged.json', source, audit, str(pdk), repaired=source,
           sta_grt_adjustment=cfg['GRT_ADJUSTMENT'])
    timing_gate(json.loads((audit / 'comparison.json').read_text()))
    if before != {str(p): digest(p) for p in paths}:
        raise ValueError('Read-only recheck changed source')
    admit_failure(saved_screen(root))
    route_dir = output / 'route'
    run_step(dict(cfg, OPENROAD_THREADS=4, DRT_SAVE_DRC_REPORT_ITERS=1, DRT_SAVE_SNAPSHOTS=True),
             source, route_dir, ['OpenROAD.DetailedRouting'])
    routed_config = json.loads((route_dir / 'resolved.json').read_text())
    if (routed_config.get('DRT_ANTENNA_REPAIR_ITERS') != 3
            or not routed_config.get('DIODE_CELL')):
        raise ValueError('Native post-DRT antenna repair defaults were not exercised')
    final = route_checkpoint(route_dir)
    validate_final_route(source, route_dir)
    checks = output / 'final-native-checks'
    run_step(cfg, final, checks, ['OpenROAD.CheckAntennas', 'Checker.TrDRC',
        'Odb.ReportDisconnectedPins', 'Checker.DisconnectedPins'])
    antenna = json.loads(one(checks, '*-openroad-checkantennas/or_metrics_out.json').read_text())
    # Antenna remains a recorded failure if nonzero; measure timing anyway on the
    # completed zero-DRC route. No failing result is converted to qualification.
    extract(route_dir, stock_constraints=True)
    extracted_state = json.loads(one(root / 'runs/extracted-timing', '*-openroad-stapostpnr/state_out.json').read_text())
    routed_state = json.loads(final.read_text())
    if logical_cells(Path(routed_state['nl']).read_text()) != logical_cells(Path(extracted_state['nl']).read_text()):
        raise ValueError('Extraction changed logical cells or connections')
    timing = json.loads((root / 'runs/extracted-timing/corner_summary.json').read_text())
    electrical = json.loads((root / 'runs/extracted-timing/electrical_summary.json').read_text())
    result = assess(timing, electrical, antenna)
    if (before != {str(p): digest(p) for p in paths}
            or inventory(root) != inventory(expected)
            or digest(root / 'src/config.json') != CONFIG_SHA):
        raise ValueError('Diagnostic modified original source views')
    result.update(source_run=SOURCE_RUN, source_sha=SOURCE_SHA, source_views=before,
                  native_stock_constraints=True, clock_uncertainty_ns=0.25,
                  logical_connectivity_preserved=True,
                  extracted_timing=timing, extracted_electrical=electrical, final_antenna=antenna)
    (output / 'diagnostic_result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    if not result['final_measured_gates_passed']:
        raise SystemExit('Diagnostic final checks fail; actual measurements retained')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('prepare', 'restore', 'measure'))
    args = parser.parse_args()
    expected = Path(os.environ['CLOSURE_EXPECTED_SOURCE'])
    if args.stage == 'prepare':
        expected_source(expected)
    elif args.stage == 'restore':
        context(json.loads(Path('closure-source-run.json').read_text()),
                json.loads(Path('closure-source-artifact.json').read_text()))
        frozen = Path.cwd() / 'closure-frozen'
        unpack(Path('closure-source.zip'), dict(digest=ARCHIVE_SHA), frozen, EXTRA_ROOTS)
        restore_source(Path.cwd(), frozen, expected)
    else:
        measure(Path.cwd())

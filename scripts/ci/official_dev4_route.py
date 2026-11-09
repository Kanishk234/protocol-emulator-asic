"""Continue the exact passing 8x4 dev4 screen through DRT and extraction."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from electrical_incremental_route import electrical_clean
from native_stock_route import qualified, run_step
from official_nov9_preflight import PDK, TOOLS, inventory
from physical_runtime import container_flags
from postgrt_timing import CORNERS, screen
from sram_bank_clean_route import validate_final_route
from sram_bank_clean_route import unique

SOURCE_RUN = 42681697462
SOURCE_SHA = '5407d4c278353ec125018f3a3d49de2fd620d9ce'
SOURCE_WORKFLOW = '.github/workflows/gds-official-dev4-hold125-screen.yaml'
RUNNER_ROOT = Path('/home/runner/work/protocol-emulator-asic/protocol-emulator-asic')


def verify_source():
    if Path.cwd().resolve() != RUNNER_ROOT:
        raise ValueError('Unexpected runner checkout root; saved state paths would be invalid')
    run = json.loads(Path('official-dev4-source-run.json').read_text())
    expected = dict(id=SOURCE_RUN, head_sha=SOURCE_SHA, head_branch='main',
                    conclusion='success', path=SOURCE_WORKFLOW)
    if any(run.get(key) != value for key, value in expected.items()):
        raise ValueError('The downloaded screen run is not the exact passing source run')
    receipt = json.loads(Path('compatibility-input.json').read_text())
    if receipt.get('tiles') != '8x4' or receipt.get('tools_sha') != TOOLS:
        raise ValueError('Screen artifact is not bound to the reviewed 8x4/dev4 toolchain')
    if receipt.get('pdk_revision') != PDK:
        raise ValueError('Screen artifact uses a different PDK revision')
    if inventory(Path('.')) != receipt.get('inputs'):
        raise ValueError('Source or macro inventory differs from the screened inputs')
    config = Path('src/config.json')
    if hashlib.sha256(config.read_bytes()).hexdigest() != receipt.get('project_config_sha256'):
        raise ValueError('Project config differs from the screened config')
    import yaml
    info = yaml.safe_load(Path('info.yaml').read_text())
    if info['project']['tiles'] != '8x4':
        raise ValueError('Screen artifact does not describe the confirmed 8x4 project')
    generated = json.loads(Path('compatibility-generated.json').read_text())
    engine = json.loads(Path('compatibility-engine.json').read_text())
    if (generated.get('generation_passed') is not True
            or generated.get('tiles') != '8x4'
            or engine.get('librelane') != '3.1.0.dev4'
            or engine.get('pdk_revision') != PDK
            or engine.get('tools_sha') != TOOLS):
        raise ValueError('Official dev4 8x4 generation/engine provenance is incomplete')
    qualification = json.loads(Path('runs/stock-corner-audit/screen_qualification.json').read_text())
    if (qualification.get('qualified') is not True
            or qualification.get('final_global_overflow') != 0
            or qualification.get('minimum_fast_hold_ns') != .05
            or qualification.get('detailed_routing_performed') is not False
            or qualification.get('official_gds_signoff') is not False):
        raise ValueError('Screen artifact does not contain the complete passing pre-route gate')
    from stock_screen_gate import qualify as requalify_screen
    repeated = requalify_screen(Path('runs/stock-official-baseline'),
                                Path('runs/stock-corner-audit'))
    if repeated.get('qualified') is not True:
        raise ValueError('Independent source-artifact gate recheck failed: ' + str(repeated.get('failures')))
    source = unique(Path('runs/stock-official-baseline'), '*-openroad-stamidpnr-3/state_out.json')
    if Path(qualification.get('source_state', '')).resolve() != source.resolve():
        raise ValueError('Screen qualification is not bound to the final pre-route checkpoint')
    state = json.loads(source.read_text())
    for key in ('odb', 'def', 'nl', 'pnl', 'sdc'):
        path = Path(state[key])
        if not path.is_file() or not path.resolve().is_relative_to(RUNNER_ROOT):
            raise ValueError(f'Missing or unsafe source checkpoint view: {key}')
    return source, json.loads(Path('src/config_merged.json').read_text())


def bootstrap_ciel_antenna(config, source, output_name='dev4-ciel-antenna'):
    """Acquire the pinned Ciel PDK via the stock backend and get a fresh antenna check."""
    output = Path('runs') / output_name
    output.mkdir(parents=True, exist_ok=False)
    cfg = dict(config)
    cfg['meta'] = {'version': config.get('meta', {}).get('version', 1),
                   'flow': ['OpenROAD.CheckAntennas']}
    path = Path('src/config_dev4_ciel_antenna.json')
    path.write_text(json.dumps(cfg, indent=2) + '\n')
    subprocess.run([sys.executable, '-m', 'librelane', '--pdk-root', '/home/runner/pdk',
                    *container_flags(), '--pdk', 'ihp-sg13cmos5l', '--run-tag', output.name,
                    '--force-run-dir', str(output), '--hide-progress-bar',
                    '--with-initial-state', str(source), str(path)], check=True)
    resolved = json.loads((output / 'resolved.json').read_text())
    pdk_root = Path(resolved['PDK_ROOT']).resolve()
    if pdk_root.name != PDK or not (pdk_root / 'ihp-sg13cmos5l').is_dir():
        raise ValueError('Ciel did not resolve the screen’s exact PDK revision')
    os.environ['PDK_ROOT'] = str(pdk_root)
    antenna = json.loads(unique(output, '*-openroad-checkantennas/or_metrics_out.json').read_text())
    if antenna.get('antenna__violating__nets') != 0 or antenna.get('antenna__violating__pins') != 0:
        raise ValueError(f'Fresh source-checkpoint antenna gate failed: {antenna}')
    return antenna


def prepare():
    source, config = verify_source()
    antenna = bootstrap_ciel_antenna(config, source)
    fresh = Path('runs/dev4-pre-route-timing')
    screen(Path('src/config_merged.json'), source, fresh, os.environ['PDK_ROOT'],
           repaired=source, sdc=Path('src/signoff.sdc'),
           sta_grt_adjustment=config['GRT_ADJUSTMENT'])
    comparison = json.loads((fresh / 'comparison.json').read_text())
    pre_route_ready = qualified(comparison, antenna) and electrical_clean(comparison)
    receipt = dict(source_run=SOURCE_RUN, source_sha=SOURCE_SHA, source_state=str(source),
                   fresh_antenna=antenna, qualified=pre_route_ready,
                   minimum_fast_hold_ns=.05, detailed_routing_performed=False,
                   official_gds_signoff=False)
    Path('runs/dev4-pre-route-gates.json').write_text(json.dumps(receipt, indent=2) + '\n')
    if not pre_route_ready:
        raise ValueError('Fresh all-corner timing/electrical/antenna gates fail; DRT refused')


def route():
    source, config = verify_source()
    receipt = json.loads(Path('runs/dev4-pre-route-gates.json').read_text())
    if (receipt.get('source_run') != SOURCE_RUN or receipt.get('source_sha') != SOURCE_SHA
            or receipt.get('qualified') is not True
            or Path(receipt.get('source_state', '')).resolve() != source.resolve()):
        raise ValueError('Missing or mismatched fresh pre-route qualification')
    route = Path('runs/dev4-hold125-route')
    run_step(config, source, route, ['OpenROAD.DetailedRouting'])
    route_state_path = unique(route, '*-openroad-detailedrouting/state_out.json')
    route_state = json.loads(route_state_path.read_text())
    if route_state.get('metrics', {}).get('route__drc_errors') != 0:
        raise ValueError('Completed DRT did not report zero route DRC errors')
    validate_final_route(source, route)
    (route / 'route_completion.json').write_text(json.dumps(dict(
        completed=True, route_drc_errors=0, source_run=SOURCE_RUN, source_sha=SOURCE_SHA,
        workflow_run_id=os.environ.get('GITHUB_RUN_ID'),
        extracted_timing_performed=False, official_gds_signoff=False), indent=2) + '\n')


def extract():
    source, config = verify_source()
    route = Path('runs/dev4-hold125-route')
    route_state_path = unique(route, '*-openroad-detailedrouting/state_out.json')
    completion = json.loads((route / 'route_completion.json').read_text())
    if (completion.get('completed') is not True or completion.get('route_drc_errors') != 0
            or completion.get('source_run') != SOURCE_RUN
            or completion.get('source_sha') != SOURCE_SHA
            or completion.get('workflow_run_id') != os.environ.get('GITHUB_RUN_ID')):
        raise ValueError('Detailed-route artifact is incomplete or from another workflow run')
    # Reinitialize the exact Ciel revision in this new job and independently
    # reconfirm the immutable screen checkpoint before extracted STA.
    bootstrap_ciel_antenna(config, source, output_name='dev4-extract-ciel-antenna')
    # The extraction helper deliberately requires the final normal PDK path.
    Path('src/config_merged.json').write_text(json.dumps(config, indent=2) + '\n')
    from extracted_timing import main as extract
    extract(route)
    extracted = Path('runs/extracted-timing')
    summary = json.loads((extracted / 'corner_summary.json').read_text())
    electrical = json.loads((extracted / 'electrical_summary.json').read_text())
    final_antenna = json.loads(unique(extracted, '*-openroad-checkantennas/or_metrics_out.json').read_text())
    failures = []
    for corner in CORNERS:
        for kind in ('setup', 'hold'):
            key = f'timing__{kind}__ws__corner:{corner}'
            minimum = .05 if kind == 'hold' and corner == CORNERS[0] else 0
            value = summary.get(key)
            if (type(value) not in (int, float) or
                    (value <= 0 if kind == 'setup' else value < minimum)):
                threshold = '> 0 ns' if kind == 'setup' else f'>= {minimum} ns'
                failures.append(f'{corner} {kind}: {value} must be {threshold}')
    if set(electrical) != set(CORNERS) or any(
            row.get('no_reported_electrical_violations') is not True for row in electrical.values()):
        failures.append('extracted electrical reports are incomplete or nonzero')
    if (final_antenna.get('antenna__violating__nets') != 0
            or final_antenna.get('antenna__violating__pins') != 0):
        failures.append(f'extracted antenna violations: {final_antenna}')
    result = dict(qualified=not failures, source_run=SOURCE_RUN, route_state=str(route_state_path),
                  extracted_timing=summary, extracted_electrical=electrical,
                  extracted_antenna=final_antenna, failures=failures,
                  official_gds_signoff=False)
    Path('runs/dev4-extracted-gates.json').write_text(json.dumps(result, indent=2) + '\n')
    if failures:
        raise ValueError('Extracted signoff gates fail: ' + '; '.join(failures))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('prepare', 'route', 'extract'))
    globals()[parser.parse_args().stage]()

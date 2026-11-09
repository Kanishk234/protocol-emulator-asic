"""Continue the exact current dev4 8x4 screen, only after strict qualification.

No repair, placement, rerouting policy or timing exception is introduced here.
The frozen source screen and fresh read-only checks must both pass before DRT.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import zipfile

from official_nov9_preflight import inventory, PDK, TOOLS, SIZES
from postgrt_timing import CORNERS, screen
from stock_screen_gate import qualify, one

SOURCE_RUN = 42681697462
SOURCE_SHA = '5407d4c278353ec125018f3a3d49de2fd620d9ce'
CONFIG_SHA = '4d71243f672fac34f004c43a8c8bfc46cffaae2b2929f7d3c788de1fac72a9f7'
IMAGE = 'ghcr.io/librelane/librelane:3.1.0.dev4'
IMAGE_DIGEST = 'sha256:af2405f5d48d8fe14d406ecce913811177a95e365e3b625859677307cace2469'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def provenance(run, artifact):
    expected = dict(id=SOURCE_RUN, head_sha=SOURCE_SHA, head_branch='main',
                    path='.github/workflows/gds-official-dev4-hold125-screen.yaml',
                    status='completed', conclusion='success', run_attempt=1)
    if any(run.get(k) != v for k, v in expected.items()):
        raise ValueError('Source screen is not the exact successful reviewed run')
    if (artifact.get('name') != f'official-dev4-hold125-{SOURCE_RUN}'
            or artifact.get('expired') is not False
            or artifact.get('workflow_run', {}).get('id') != SOURCE_RUN
            or artifact.get('workflow_run', {}).get('head_sha') != SOURCE_SHA):
        raise ValueError('Wrong or expired source artifact')
    value = artifact.get('digest', '')
    if not isinstance(value, str) or not value.startswith('sha256:') or len(value) != 71:
        raise ValueError('Missing whole-archive API digest')


def unpack(archive, artifact, output):
    if 'sha256:' + digest(archive) != artifact['digest']:
        raise ValueError('Whole source archive digest mismatch')
    if output.exists():
        raise ValueError('Refusing an existing extraction directory')
    with zipfile.ZipFile(archive) as bundle:
        names = set()
        for info in bundle.infolist():
            path = PurePosixPath(info.filename)
            mode = info.external_attr >> 16
            if (path.is_absolute() or '..' in path.parts or '\\' in info.filename
                    or not path.parts or (path.parts[0] not in (
                        'runs', 'src', 'macro', 'spikes', 'info.yaml')
                    and not path.parts[0].startswith('compatibility-'))
                    or stat.S_ISLNK(mode) or str(path) in names):
                raise ValueError('Unsafe or duplicate source archive entry')
            names.add(str(path))
        output.mkdir()
        bundle.extractall(output)


def timing_gate(comparison):
    if set(comparison.get('corners', {})) != set(CORNERS):
        raise ValueError('Missing or unexpected timing corner')
    for corner in CORNERS:
        for stage in ('before', 'after'):
            row = comparison['corners'][corner][stage]
            for kind in ('setup', 'hold'):
                value = row[f'timing__{kind}__ws__corner:{corner}']
                minimum = 0.05 if kind == 'hold' and corner == CORNERS[0] else 0
                if type(value) not in (int, float) or not math.isfinite(value) or value < minimum:
                    raise ValueError('Timing gate fails: ' + corner + ' ' + kind)
            for kind in ('slew', 'cap', 'fanout'):
                value = row[f'design__max_{kind}_violation__count__corner:{corner}']
                if type(value) is not int or value != 0:
                    raise ValueError('Electrical gate fails: ' + corner + ' ' + kind)


def restore(root, frozen, expected):
    if inventory(frozen) != inventory(expected):
        raise ValueError('Artifact hardware/macro bytes differ from prepared source')
    for name in ('src/config.json', 'info.yaml'):
        if digest(frozen / name) != digest(expected / name):
            raise ValueError('Artifact project inputs differ: ' + name)
    if digest(frozen / 'src/config.json') != CONFIG_SHA:
        raise ValueError('Wrong hold125 project configuration')
    engine = json.loads((frozen / 'compatibility-engine.json').read_text())
    if any(engine.get(k) != v for k, v in dict(
            librelane='3.1.0.dev4', pdk_revision=PDK, tools_sha=TOOLS).items()):
        raise ValueError('Wrong frozen engine')
    images = json.loads((frozen / 'compatibility-image.json').read_text())
    if len(images) != 1 or IMAGE.rsplit(':', 1)[0] + '@' + IMAGE_DIGEST not in images[0]['RepoDigests']:
        raise ValueError('Wrong frozen container identity')
    physical = root / 'runs/stock-official-baseline'
    if (root / 'runs').exists():
        raise ValueError('Restoration needs a fresh physical workspace')
    source = one(frozen / 'runs/stock-official-baseline', '*-openroad-stamidpnr-3/state_out.json')
    receipt = json.loads((frozen / 'runs/stock-corner-audit/read_only_audit.json').read_text())
    if receipt['source_state'] != str(root / source.relative_to(frozen)):
        raise ValueError('Runner path differs; saved states must not be rewritten')
    cfg = json.loads((frozen / 'src/config_merged.json').read_text())
    if (cfg['DIE_AREA'] != SIZES['8x4'] or cfg['CLOCK_PERIOD'] != 20
            or cfg['RT_MAX_LAYER'] != 'Metal4'):
        raise ValueError('Wrong merged physical platform')
    for folder in ('src', 'macro'):
        shutil.copytree(frozen / folder, root / folder, dirs_exist_ok=True)
    shutil.copy2(frozen / 'info.yaml', root / 'info.yaml')
    shutil.copytree(frozen / 'runs', root / 'runs')
    result = qualify(physical, root / 'runs/stock-corner-audit')
    if result['qualified'] is not True:
        raise ValueError('Saved native screen fails: ' + str(result['failures']))
    signoff = json.loads((root / 'runs/stock-signoff-estimate/qualification.json').read_text())
    if signoff.get('qualified') is not True or signoff.get('failures') != []:
        raise ValueError('Saved signoff estimate is not qualified')
    source = one(physical, '*-openroad-stamidpnr-3/state_out.json')
    state = json.loads(source.read_text())
    paths = [source, root / 'src/signoff.sdc'] + [Path(state[k]) for k in ('odb', 'def', 'nl', 'pnl', 'sdc')]
    hashes = {str(p): digest(p) for p in paths}
    if signoff['unchanged_source_hashes'] != hashes:
        raise ValueError('Signoff estimate does not bind the restored source')
    timing_gate(json.loads((root / 'runs/stock-signoff-estimate/comparison.json').read_text()))
    result.update(source_run=SOURCE_RUN, source_sha=SOURCE_SHA,
                  saved_state_rewritten=False, physical_repairs_performed=False)
    (root / 'runs/closure-restoration.json').write_text(json.dumps(result, indent=2) + '\n')
    return source


def route(root):
    from native_stock_route import run_step
    from sram_bank_clean_route import validate_final_route
    from extracted_timing import route_checkpoint, main as extract

    source = one(root / 'runs/stock-official-baseline', '*-openroad-stamidpnr-3/state_out.json')
    restoration = json.loads((root / 'runs/closure-restoration.json').read_text())
    if (restoration.get('qualified') is not True or restoration.get('source_run') != SOURCE_RUN
            or restoration.get('source_sha') != SOURCE_SHA):
        raise ValueError('Missing qualified restoration')
    expected = Path(os.environ['CLOSURE_EXPECTED_SOURCE'])
    if inventory(root) != inventory(expected) or digest(root / 'src/config.json') != CONFIG_SHA:
        raise ValueError('Source changed after restoration')
    if digest(root / 'info.yaml') != digest(expected / 'info.yaml'):
        raise ValueError('Metadata changed after restoration')
    cfg_path = root / 'src/config_merged.json'
    cfg = json.loads(cfg_path.read_text())
    # A first check step with normal Ciel selection is run by the workflow.
    initial = root / 'runs/closure-initialize'
    resolved = json.loads((initial / 'resolved.json').read_text())
    pdk = Path(resolved['PDK_ROOT'])
    if pdk.name != PDK or not (pdk / 'ihp-sg13cmos5l').is_dir():
        raise ValueError('Wrong Ciel-selected PDK')
    os.environ['PDK_ROOT'] = str(pdk)
    initial_antenna = json.loads(one(initial, '*-openroad-checkantennas/or_metrics_out.json').read_text())
    if any(type(initial_antenna.get(k)) is not int or initial_antenna[k] != 0
           for k in ('antenna__violating__nets', 'antenna__violating__pins')):
        raise ValueError('Fresh restored source antenna check fails')
    source_state = json.loads(source.read_text())
    paths = [source] + [Path(source_state[k]) for k in ('odb', 'def', 'nl', 'pnl', 'sdc')]
    before = {str(p): digest(p) for p in paths}
    for label, constraints in (('original', None), ('signoff', root / 'src/signoff.sdc')):
        output = root / ('runs/closure-fresh-' + label)
        screen(cfg_path, source, output, str(pdk), repaired=source,
               sdc=constraints, sta_grt_adjustment=cfg['GRT_ADJUSTMENT'])
        timing_gate(json.loads((output / 'comparison.json').read_text()))
    if before != {str(p): digest(p) for p in paths}:
        raise ValueError('Read-only checks changed source views')
    saved = qualify(root / 'runs/stock-official-baseline', root / 'runs/stock-corner-audit')
    if saved['qualified'] is not True:
        raise ValueError('Restored source drifted before routing')
    route_cfg = dict(cfg, OPENROAD_THREADS=4, DRT_SAVE_DRC_REPORT_ITERS=1, DRT_SAVE_SNAPSHOTS=True)
    output = root / 'runs/closure-route'
    run_step(route_cfg, source, output, ['OpenROAD.DetailedRouting'])
    final = route_checkpoint(output)
    validate_final_route(source, output)
    run_step(route_cfg, final, root / 'runs/closure-route-checks', [
        'OpenROAD.CheckAntennas', 'Checker.TrDRC', 'Odb.ReportDisconnectedPins', 'Checker.DisconnectedPins'])
    antenna = json.loads(one(root / 'runs/closure-route-checks', '*-openroad-checkantennas/or_metrics_out.json').read_text())
    if any(type(antenna.get(k)) is not int or antenna[k] != 0
           for k in ('antenna__violating__nets', 'antenna__violating__pins')):
        raise ValueError('Final routed antenna gate fails')
    extract(output)
    timing = json.loads((root / 'runs/extracted-timing/corner_summary.json').read_text())
    electrical = json.loads((root / 'runs/extracted-timing/electrical_summary.json').read_text())
    rows = {}
    for corner in CORNERS:
        row = dict(timing)
        for kind, key in (('slew', 'slew'), ('cap', 'capacitance'), ('fanout', 'fanout')):
            row[f'design__max_{kind}_violation__count__corner:{corner}'] = electrical[corner]['counts'][key]
        rows[corner] = {'before': row, 'after': row}
    timing_gate({'corners': rows})
    (output / 'completion.json').write_text(json.dumps(dict(
        source_run=SOURCE_RUN, source_sha=SOURCE_SHA, source_views=before,
        detailed_routing_completed=True, extracted_timing_passed=True,
        final_antenna_nets=0, final_antenna_pins=0, route_drc_errors=0,
        disconnected_pin_checker_passed=True, minimum_fast_hold_ns=0.05,
        official_gds_signoff=False, routed_protocol_replay_performed=False), indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('restore', 'route'))
    args = parser.parse_args()
    root = Path.cwd()
    if args.stage == 'restore':
        run = json.loads(Path('closure-source-run.json').read_text())
        artifact = json.loads(Path('closure-source-artifact.json').read_text())
        provenance(run, artifact)
        frozen = root / 'closure-frozen'
        unpack(root / 'closure-source.zip', artifact, frozen)
        restore(root, frozen, Path(os.environ['CLOSURE_EXPECTED_SOURCE']))
    else:
        route(root)

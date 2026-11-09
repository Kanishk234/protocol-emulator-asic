"""Read-only operating-period sensitivity on the exact failed extracted route.

The original 20 ns failure stays failed. This never changes production RTL,
the clock contract, physical placement/routing, or a release acceptance gate.
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

from closure_final_gl import ROUTE_RUN, ROUTE_SHA, source_context
from closure_route import digest, CONFIG_SHA, PDK
from official_nov9_preflight import inventory
from postgrt_timing import CORNERS

ARTIFACT_ID = 13716989088
ARCHIVE_SHA = 'sha256:08c1b4d5ef59066d42f35fc1690fe96d79b95af8fb71cbc6a4200b993605664a'
PERIODS = (20, 21, 22, 24, 25)
REFERENCE = {
    'nom_fast_1p32V_m40C': (0, 0.2839847326566228),
    'nom_slow_1p08V_125C': (-1.9824480396180877, 0.8670655550077222),
    'nom_typ_1p20V_25C': (0, 0.5014901968969487),
}


def selected_member(name):
    # State.load validates inherited header views even for a read-only ODB step.
    return (name.startswith(('src/', 'macro/', 'runs/extracted-timing/',
                'runs/closure-route-checks/',
                'runs/stock-official-baseline/05-yosys-jsonheader/',
                'runs/stock-official-baseline/29-odb-writeverilogheader/'))
            or name == 'info.yaml'
            or name.startswith('runs/closure-route/') and name.endswith('/state_out.json'))


def context(run, artifact):
    source_context(run, artifact, completed=False)
    if (run.get('status') != 'completed' or run.get('conclusion') != 'failure'
            or artifact.get('id') != ARTIFACT_ID or artifact.get('digest') != ARCHIVE_SHA):
        raise ValueError('Expected the exact retained failed extraction source')


def configure(original, period, sdc):
    if (period not in PERIODS or type(period) is not int or original.get('CLOCK_PERIOD') != 20
            or original.get('STA_EXTRA_CORNER_TCL_FILE') not in (None, '')):
        raise ValueError('Unreviewed diagnostic operating period')
    result = dict(original, CLOCK_PERIOD=period, STA_CORNERS=list(CORNERS), STA_THREADS=3,
                  SIGNOFF_SDC_FILE=str(sdc.resolve()))
    result.pop('STA_EXTRA_CORNER_TCL_FILE', None)
    return result


def reference_matches(reference):
    expected = {f'timing__{kind}__ws__corner:{c}': value
                for c, pair in REFERENCE.items() for kind, value in zip(('setup', 'hold'), pair)}
    if set(reference) != set(expected): raise ValueError('Wrong original extracted corner set')
    if any(type(reference[k]) not in (int, float) or not math.isfinite(reference[k])
           or abs(reference[k] - value) > 1e-9 for k, value in expected.items()):
        raise ValueError('Wrong original extracted failure')


def restore(root, archive, expected):
    if 'sha256:' + digest(archive) != ARCHIVE_SHA:
        raise ValueError('Failed-route archive digest mismatch')
    if (root / 'runs').exists(): raise ValueError('Diagnostic recovery needs a fresh workspace')
    with zipfile.ZipFile(archive) as bundle:
        seen = set()
        for info in bundle.infolist():
            p = PurePosixPath(info.filename)
            if (p.is_absolute() or '..' in p.parts or '\\' in info.filename
                    or str(p) in seen or stat.S_ISLNK(info.external_attr >> 16)):
                raise ValueError('Unsafe route archive member')
            seen.add(str(p))
            selected = selected_member(info.filename)
            if selected and not info.is_dir():
                target = root / str(p)
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(info) as source, target.open('wb') as out:
                    shutil.copyfileobj(source, out)
    if inventory(root) != inventory(expected) or digest(root / 'src/config.json') != CONFIG_SHA:
        raise ValueError('Failed-route source differs from prepared hardware')
    if (root / 'info.yaml').read_bytes() != (expected / 'info.yaml').read_bytes():
        raise ValueError('Failed-route metadata differs')
    route = list((root / 'runs/closure-route').glob('*-openroad-detailedrouting/state_out.json'))
    if len(route) != 1 or json.loads(route[0].read_text())['metrics'].get('route__drc_errors') != 0:
        raise ValueError('A completed zero-DRC route is required')
    antenna = list((root / 'runs/closure-route-checks').glob('*-openroad-checkantennas/or_metrics_out.json'))
    if len(antenna) != 1: raise ValueError('Missing final antenna report')
    values = json.loads(antenna[0].read_text())
    if any(type(values.get(k)) is not int or values[k] != 0
           for k in ('antenna__violating__nets', 'antenna__violating__pins')):
        raise ValueError('Final antenna result is not clean')
    reference = json.loads((root / 'runs/extracted-timing/corner_summary.json').read_text())
    reference_matches(reference)
    (root / 'runs/clock-probe-recovery.json').write_text(json.dumps(dict(
        source_run=ROUTE_RUN, source_sha=ROUTE_SHA, archive_sha256=ARCHIVE_SHA,
        physical_change_applied=False, original_20ns_qualified=False), indent=2) + '\n')


def measure(root):
    from native_stock_route import run_step
    from extracted_sizing_sensitivity import sta_input_state, corner_metrics, baseline_matches
    source = list((root / 'runs/extracted-timing').glob('*-openroad-stapostpnr/state_out.json'))
    if len(source) != 1: raise ValueError('Missing completed extracted STA state')
    state = json.loads(source[0].read_text())
    sdc = root / 'runs/extracted-timing/effective-signoff.sdc'
    if digest(sdc) != '63a9ac8dc9d00741c26ea37cf8ee01345c2ebf178e1c408dd213619e080d0ffa':
        raise ValueError('Effective signoff constraints changed')
    nl = Path(state['nl'])
    paths = [source[0], nl, Path(state['odb']), sdc,
             root / 'src/config.json', root / 'src/config_extracted_timing.json']
    paths += [Path(p) for p in state['spef'].values()]
    if not state.get('spef') or any(not p.is_file() for p in paths):
        raise ValueError('Missing exact fixed-route timing inputs')
    before = {str(p): digest(p) for p in paths}
    init = json.loads((root / 'runs/clock-probe-initialize/resolved.json').read_text())
    pdk = Path(init['PDK_ROOT'])
    if pdk.name != PDK or not (pdk / 'ihp-sg13cmos5l').is_dir():
        raise ValueError('Wrong Ciel-selected diagnostic PDK')
    os.environ['PDK_ROOT'] = str(pdk)
    antennas = list((root / 'runs/clock-probe-initialize').glob('*-openroad-checkantennas/or_metrics_out.json'))
    if len(antennas) != 1: raise ValueError('Missing fresh diagnostic antenna control')
    ant = json.loads(antennas[0].read_text())
    if any(type(ant.get(k)) is not int or ant[k] != 0
           for k in ('antenna__violating__nets', 'antenna__violating__pins')):
        raise ValueError('Fresh restored antenna control fails')
    original = json.loads((root / 'src/config_extracted_timing.json').read_text())
    output = root / 'runs/closure-clock-probe'; output.mkdir(exist_ok=False)
    reference = json.loads((root / 'runs/extracted-timing/corner_summary.json').read_text())
    results = {}
    for period in PERIODS:
        config = configure(original, period, sdc)
        proposed = output / f'period-{period}.json'
        proposed.write_text(json.dumps(sta_input_state(state, nl), indent=2) + '\n')
        run_step(config, proposed, output / f'period-{period}', ['OpenROAD.STAPostPNR'])
        stages = list((output / f'period-{period}').glob('*-openroad-stapostpnr/state_out.json'))
        if len(stages) != 1: raise ValueError('Missing fresh diagnostic STA')
        metrics = corner_metrics(stages[0].parent)
        if period == 20: baseline_matches(metrics, reference)
        if before != {str(p): digest(p) for p in paths}:
            raise ValueError('Read-only sensitivity modified frozen inputs')
        results[str(period)] = metrics
        (output / 'results.json').write_text(json.dumps(dict(
            source_run=ROUTE_RUN, source_sha=ROUTE_SHA, fixed_views=before,
            baseline_20ns_reproduced=True, source_20ns_qualified=False,
            cases=results, physical_change_applied=False, physical_qualified=False,
            production_clock_changed=False, official_gds_qualified=False,
            scope='Fixed extracted RC; CLOCK_PERIOD changes stock period-derived constraints too'), indent=2) + '\n')
        print('Diagnostic period', period, json.dumps(metrics), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('restore', 'measure'))
    args = parser.parse_args()
    if args.stage == 'restore':
        context(json.loads(Path('probe-source-run.json').read_text()),
                json.loads(Path('probe-source-artifact.json').read_text()))
        restore(Path.cwd(), Path('probe-source.zip'), Path(os.environ['CLOSURE_EXPECTED_SOURCE']))
    else:
        measure(Path.cwd())

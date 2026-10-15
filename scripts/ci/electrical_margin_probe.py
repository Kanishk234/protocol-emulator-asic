"""Read-only paired GRT/extracted per-net electrical-margin diagnostic."""
import hashlib
import json
import os
from pathlib import Path
from native_stock_route import run_step
from postgrt_timing import CORNERS
from sram_bank_clean_route import unique

SOURCE_RUN = 38689478738
SOURCE_SHA = '54c32ceb682e3cbd7deb68e83c5d4b6400e0ad5f'


def input_hashes(states):
    paths = set()
    def gather(value):
        if isinstance(value, str):
            path = Path(value)
            if not path.is_file():
                raise ValueError('Missing saved probe input '+value)
            paths.add(path)
        elif isinstance(value, dict):
            for v in value.values(): gather(v)
        elif isinstance(value, list):
            for v in value: gather(v)
    for state in states.values():
        paths.add(state)
        values = json.loads(state.read_text())
        for key in ('odb', 'def', 'nl', 'pnl', 'sdc', 'spef'):
            if values.get(key) is not None: gather(values[key])
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def validate_source(run, gates):
    expected = dict(id=SOURCE_RUN, head_sha=SOURCE_SHA, head_branch='main',
                    conclusion='failure', path='.github/workflows/gds-route-reserve-route.yaml')
    if any(run.get(k) != v for k, v in expected.items()):
        raise ValueError('Wrong failed-route provenance')
    if gates.get('qualified') is not False or gates.get('source_run') != 38687129808:
        raise ValueError('Wrong failed extracted gate receipt')


def main():
    from electrical_margin_summary import summarize, paired
    validate_source(json.loads(Path('/tmp/native-strength-source-run.json').read_text()),
                    json.loads(Path('runs/route-reserve-route/extracted_gates.json').read_text()))
    route_state = json.loads(unique(Path('runs/route-reserve-route/drt'),
                                    '*-openroad-detailedrouting/state_out.json').read_text())
    if route_state['metrics'].get('route__drc_errors') != 0:
        raise ValueError('Probe requires completed zero-DRC route')
    config = json.loads(Path('src/config_route_reserve_screen.json').read_text())
    if float(config['CLOCK_PERIOD']) != 20:
        raise ValueError('Wrong clock period')
    sdc = Path('src/signoff.sdc').resolve()
    config.update(PNR_SDC_FILE=str(sdc), SIGNOFF_SDC_FILE=str(sdc),
        STA_EXTRA_CORNER_TCL_FILE=str(Path('workflow-src/scripts/ci/electrical_margin_probe.tcl').resolve()),
        OPENROAD_THREADS=4, STA_THREADS=1)
    states = dict(screen=unique(Path('runs/route-reserve-screen/antenna'),
                               '*-openroad-checkantennas/state_out.json'),
                  extracted=unique(Path('runs/extracted-timing'),
                                   '*-openroad-stapostpnr/state_out.json'))
    before_hashes = input_hashes(states)
    constraint_identity = json.loads(Path('runs/extracted-timing/constraint_identity.json').read_text())
    if constraint_identity['sha256'] != hashlib.sha256(sdc.read_bytes()).hexdigest():
        raise ValueError('Extracted and screen signoff constraints differ')
    root = Path('runs/electrical-margin-probe')
    root.mkdir(exist_ok=False)
    manifest = dict(source_run=SOURCE_RUN, read_only=True, official_signoff=False,
        signoff_sdc_sha256=hashlib.sha256(sdc.read_bytes()).hexdigest(), stages={})
    for tag, state in states.items():
        cfg = dict(config, PNR_CORNERS=list(CORNERS), STA_CORNERS=list(CORNERS))
        if tag == 'screen':
            # One estimated corner per process; preserve the exact saved ODB.
            for corner in CORNERS:
                run_step(dict(cfg, PNR_CORNERS=[corner]), state, root/tag/corner,
                         ['OpenROAD.STAMidPNR'])
        else:
            run_step(cfg, state, root/tag, ['OpenROAD.STAPostPNR'])
        reports = list((root/tag).rglob('electrical_margin.rpt'))
        if len(reports) != 3:
            raise ValueError('Missing per-corner margin reports')
        manifest['stages'][tag] = summarize(reports)
    if input_hashes(states) != before_hashes:
        raise ValueError('Probe modified a saved physical input')
    manifest['input_sha256'] = before_hashes
    manifest['paired'] = paired(manifest['stages']['screen'], manifest['stages']['extracted'])
    (root/'summary.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({tag: {c: v['near_limit_counts'] for c, v in corners.items()}
                      for tag, corners in manifest['stages'].items()}, indent=2))


if __name__ == '__main__':
    main()

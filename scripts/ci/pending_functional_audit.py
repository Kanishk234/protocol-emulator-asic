"""Read actual functional setup reserve on the exact failed polarity screen."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from functional_setup_frontier import parse_report
from official_nov9_preflight import PDK
from physical_runtime import container_flags
from postgrt_timing import CORNERS, screen

SOURCE_RUN = 43390348317
SOURCE_SHA = '258186504e4b9f73d2711067e456494def705d2b'
ODB_SHA = '73cae023878093e4b853ca0bffc997ba680a328de8cd6a908071e5a088781649'


def main():
    root = Path.cwd().resolve()
    expected_root = Path('/home/runner/work/protocol-emulator-asic/protocol-emulator-asic')
    if root != expected_root:
        raise ValueError('Saved state paths require the exact runner root')
    run = json.loads(Path('pending-source-run.json').read_text())
    expected = dict(id=SOURCE_RUN, head_sha=SOURCE_SHA, head_branch='main',
                    conclusion='failure', path='.github/workflows/gds-official-dev4-pending-polarity-screen.yaml')
    if any(run.get(k) != v for k, v in expected.items()):
        raise ValueError('Wrong source screen identity')
    source = Path('runs/stock-official-baseline/45-openroad-stamidpnr-3/state_out.json')
    state = json.loads(source.read_text())
    paths = [source, Path('src/signoff.sdc')] + [Path(state[k]) for k in ('odb', 'def', 'nl', 'pnl', 'sdc')]
    if any(not p.is_file() or not p.resolve().is_relative_to(root) for p in paths):
        raise ValueError('Missing or unsafe source physical view')
    if hashlib.sha256(Path(state['odb']).read_bytes()).hexdigest() != ODB_SHA:
        raise ValueError('Wrong exact source database')
    config_path = Path('src/config_merged.json')
    config = json.loads(config_path.read_text())
    if config['CLOCK_PERIOD'] != 20:
        raise ValueError('Wrong source clock')
    def hashes():
        return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    before = hashes()
    bootstrap = Path('runs/pending-functional-pdk')
    bootstrap.mkdir(parents=True, exist_ok=False)
    acquire = dict(config)
    acquire['meta'] = {'version': config.get('meta', {}).get('version', 1), 'flow': ['OpenROAD.CheckAntennas']}
    acquire_path = Path('src/config_pending_functional_pdk.json')
    acquire_path.write_text(json.dumps(acquire, indent=2)+'\n')
    subprocess.run([sys.executable, '-m', 'librelane', '--pdk-root', '/home/runner/pdk',
                    *container_flags(), '--pdk', 'ihp-sg13cmos5l', '--run-tag', bootstrap.name,
                    '--force-run-dir', str(bootstrap), '--hide-progress-bar',
                    '--with-initial-state', str(source), str(acquire_path)], check=True)
    resolved = json.loads((bootstrap/'resolved.json').read_text())
    pdk = Path(resolved['PDK_ROOT'])
    if pdk.name != PDK or not (pdk/'ihp-sg13cmos5l').is_dir():
        raise ValueError('Wrong native PDK')
    files = list(bootstrap.glob('*-openroad-checkantennas/or_metrics_out.json'))
    if len(files) != 1:
        raise ValueError('Missing source antenna measurement')
    antenna = json.loads(files[0].read_text())
    if antenna.get('antenna__violating__nets') != 1 or antenna.get('antenna__violating__pins') != 1:
        raise ValueError('Source antenna counts differ from the bound failed screen')
    output = Path('runs/pending-functional-audit')
    screen(config_path, source, output, str(pdk), repaired=source,
           extra_tcl=Path('scripts/ci/functional_setup_frontier.tcl'),
           sta_grt_adjustment=config['GRT_ADJUSTMENT'])
    comparison = json.loads((output/'comparison.json').read_text())
    baseline = json.loads(Path('runs/stock-corner-audit/read_only_audit.json').read_text())
    reports = {}
    for corner in CORNERS:
        for phase in ('before', 'after'):
            metrics = comparison['corners'][corner][phase]
            for key, value in baseline['fresh_corner_metrics'][corner].items():
                if key not in metrics or abs(metrics[key]-value) > 1e-9:
                    raise ValueError('Read-only source timing/electrical baseline changed: '+key)
            matches = list((output/f'{phase}-{corner}').glob('*-openroad-stamidpnr/functional_setup_frontier.rpt'))
            if len(matches) != 1:
                raise ValueError('Missing functional setup report')
            row = parse_report(matches[0].read_text(), corner)
            reports[f'{phase}-{corner}'] = row
        if reports[f'before-{corner}'] != reports[f'after-{corner}']:
            raise ValueError('Repeated functional path report differs')
    if hashes() != before:
        raise ValueError('Read-only audit changed source physical views')
    result = dict(source_run=SOURCE_RUN, source_sha=SOURCE_SHA, source_hashes=before,
                  functional_setup=reports, source_antenna_violations=1,
                  physical_repairs=False, detailed_routing_performed=False,
                  qualified=False, official_signoff=False)
    (output/'receipt.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

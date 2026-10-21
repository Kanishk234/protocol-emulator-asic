"""Clean-source parallel drop counter screen with verified incremental routing."""
import json
import os
from pathlib import Path
import subprocess

from native_setup_reserve_screen import main as reserve_screen
from native_no_final_grt_control import routing_objects
from native_route_trace_probe import collect
from native_wire150_screen import configure as wire_configure
from postgrt_timing import CORNERS
from sram_bank_clean_route import unique
from verify_drop_parallel import digest, TRIAL_HASH

IMAGE = 'tripwire-native-incremental-route:local'


def configure(config):
    result = wire_configure(config)
    if result.get('GRT_RESIZER_RUN_GRT', True) is not True:
        raise ValueError('Incremental routing requires the final native route branch')
    return result


def enforce_routing_objects(root):
    path = root/'gates.json'
    gates = json.loads(path.read_text())
    prior = gates['qualified']
    gates['qualified'] = False
    path.write_text(json.dumps(gates, indent=2)+'\n')
    step = unique(root/'flow', '*-openroad-resizertimingpostgrt/state_out.json').parent
    log = (step/'openroad-resizertimingpostgrt.log').read_text()
    if any(log.count('TRIPWIRE_INCREMENTAL '+m+'\n') != 1 for m in ('begin', 'end')):
        raise ValueError('Missing unique native incremental routing receipt')
    snapshots = collect(step, log)
    coverage = {c: routing_objects(unique(root/'timing'/f'after-{c}',
                '*-openroad-stamidpnr/route_coverage.rpt').read_text(), c) for c in CORNERS}
    if any(v != coverage[CORNERS[0]] for v in coverage.values()):
        raise ValueError('Route coverage differs across the same database')
    present = coverage[CORNERS[0]]['MISSING_NETS'] == 0
    gates.update(routing_object_counts=coverage, all_signal_nets_have_routing_objects=present,
                 routing_completeness_proven=False, qualified=prior and present,
                 native_incremental_tracking_verified=True, snapshots=snapshots)
    path.write_text(json.dumps(gates, indent=2)+'\n')
    if not present:
        raise ValueError('Missing signal-net routing objects; no detailed routing')


def main():
    if (os.environ.get('VARIANT') != 'bs-resync-cfg-tx-cached-lane-mask-drop-parallel'
            or digest(Path('src/trw_chan_port.v')) != TRIAL_HASH):
        raise ValueError('Wrong verified parallel counter variant')
    run_screen()


def run_screen(*, config_transform=configure):
    """Execute unchanged strict screen after the caller validates its source."""
    subprocess.run(['docker', 'build', '-t', IMAGE, '-f',
                    'workflow-src/scripts/ci/Dockerfile.openroad-native-incremental',
                    'workflow-src/scripts/ci'], check=True)
    root = Path('runs/native-stock-screen')
    try:
        reserve_screen(config_transform=config_transform, image_override=IMAGE,
                       audit_tcl=Path('workflow-src/scripts/ci/native_no_final_grt_audit.tcl'))
    except Exception:
        if (root/'gates.json').is_file():
            try:
                path = root/'gates.json'
                gates = json.loads(path.read_text())
                gates['qualified'] = False
                path.write_text(json.dumps(gates, indent=2)+'\n')
                enforce_routing_objects(root)
            except Exception as error:
                print(f'Additional route coverage result: {error}', flush=True)
        raise
    enforce_routing_objects(root)


if __name__ == '__main__':
    main()

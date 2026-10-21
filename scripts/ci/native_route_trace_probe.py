"""Exact-source native route-stage snapshots; no qualification or DRT authority."""
import json
import os
from pathlib import Path
import subprocess

from native_lane_mask_stage_probe import PROFILE
from native_no_final_grt_control import configure, SOURCE_STAGE, SOURCE_ODB_HASH
from native_route_trace import STAGES
from native_stage_probe import digest, validate
from native_stock_route import run_step
from sram_bank_clean_route import unique

OUTPUT = Path('runs/native-route-trace')


def collect(root, log):
    records = {}
    for stage in STAGES:
        if log.count('TRIPWIRE_ROUTE_SNAPSHOT '+stage+'\n') != 1:
            raise ValueError('Missing or repeated native route snapshot: '+stage)
        paths = [root/'route_trace'/stage/('snapshot.'+ext) for ext in ('odb', 'def', 'v')]
        if stage in ('initial_route', 'final_route'):
            paths.append(root/'route_trace'/stage/'after_grt.guide')
        if any(not p.is_file() or p.stat().st_size == 0 for p in paths):
            raise ValueError('Missing native route snapshot views: '+stage)
        records[stage] = {p.name: dict(path=str(p), sha256=digest(p)) for p in paths}
    return records


def main():
    config = json.loads(Path('src/config_native_stock.json').read_text())
    validate(json.loads(Path('/tmp/native-source-run.json').read_text()), config, PROFILE)
    configure(config)  # Validate exact recipe, discard the disabled-GRT variant.
    source = Path('runs/native-stock-screen/flow')/SOURCE_STAGE/'state_out.json'
    odb = Path(json.loads(source.read_text())['odb'])
    if (not odb.resolve().is_relative_to(source.parent.resolve())
            or odb.name != 'tt_um_tripwire.odb' or digest(odb) != SOURCE_ODB_HASH):
        raise ValueError('Wrong exact pre-hold database')
    OUTPUT.mkdir(exist_ok=False)
    image = 'tripwire-native-route-trace:local'
    subprocess.run(['docker', 'build', '-t', image, '-f',
                    'workflow-src/scripts/ci/Dockerfile.openroad-route-trace',
                    'workflow-src/scripts/ci'], check=True)
    os.environ['LIBRELANE_IMAGE_OVERRIDE'] = image
    # Preserve native final GRT and antenna repair; no relaxed route policy.
    run_step(config, source, OUTPUT/'flow',
             ['OpenROAD.ResizerTimingPostGRT', 'OpenROAD.RepairAntennas'])
    step = unique(OUTPUT/'flow', '*-openroad-resizertimingpostgrt/state_out.json').parent
    snapshots = collect(step, (step/'openroad-resizertimingpostgrt.log').read_text())
    final = unique(OUTPUT/'flow', '*-openroad-repairantennas/state_out.json')
    if digest(odb) != SOURCE_ODB_HASH:
        raise ValueError('Source database changed')
    receipt = dict(diagnostic_only=True, qualified=False, route_authorized=False,
                   official_signoff=False, source_run=PROFILE['source_run'],
                   source_sha=PROFILE['source_sha'], source_odb_sha256=SOURCE_ODB_HASH,
                   native_final_reroute=True, final_state=str(final), snapshots=snapshots)
    (OUTPUT/'diagnosis.json').write_text(json.dumps(receipt, indent=2)+'\n')


if __name__ == '__main__':
    main()

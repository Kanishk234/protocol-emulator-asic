"""Checkpoint control of native incremental routing through repair; never signoff."""
import json
import os
from pathlib import Path
import subprocess

from electrical_margin_gate import measure
from event_nor2_screen import validate_overflow
from native_lane_mask_stage_probe import PROFILE
from native_margin_screen import audit_post_antenna, check_post_antenna_command, evaluate
from native_no_final_grt_control import (SOURCE_STAGE, SOURCE_ODB_HASH, configure,
                                        record_capture, routing_objects)
from native_route_trace_probe import collect
from native_stage_probe import digest, validate
from native_stock_route import run_step
from postgrt_timing import CORNERS, screen
from sram_bank_clean_route import unique

OUTPUT = Path('runs/native-incremental-route-control')


def record_control_image(gates, image):
    if gates.get('qualified') is not False or gates.get('diagnostic_only') is not True:
        raise ValueError('Incremental image metadata requires a diagnostic-only receipt')
    return dict(gates, custom_image=True, custom_image_name=image,
                native_routing_modified=True)


def main():
    original = json.loads(Path('src/config_native_stock.json').read_text())
    validate(json.loads(Path('/tmp/native-source-run.json').read_text()), original, PROFILE)
    configure(original)  # Validate stock full-route source policy.
    config = dict(original)
    source = Path('runs/native-stock-screen/flow')/SOURCE_STAGE/'state_out.json'
    source_odb = Path(json.loads(source.read_text())['odb'])
    if (source_odb.name != 'tt_um_tripwire.odb'
            or not source_odb.resolve().is_relative_to(source.parent.resolve())
            or digest(source_odb) != SOURCE_ODB_HASH):
        raise ValueError('Wrong exact pre-hold control database')
    OUTPUT.mkdir(exist_ok=False)
    image = 'tripwire-native-incremental-route:local'
    subprocess.run(['docker', 'build', '-t', image, '-f',
                    'workflow-src/scripts/ci/Dockerfile.openroad-native-incremental',
                    'workflow-src/scripts/ci'], check=True)
    os.environ['LIBRELANE_IMAGE_OVERRIDE'] = image
    run_step(config, source, OUTPUT/'flow',
             ['OpenROAD.ResizerTimingPostGRT', 'OpenROAD.RepairAntennas'])
    prior = unique(OUTPUT/'flow', '*-openroad-resizertimingpostgrt/state_out.json')
    raw = unique(OUTPUT/'flow', '*-openroad-repairantennas/state_out.json')
    log = (prior.parent/'openroad-resizertimingpostgrt.log').read_text()
    if any(log.count('TRIPWIRE_INCREMENTAL '+marker+'\n') != 1 for marker in ('begin', 'end')):
        raise ValueError('Missing unique incremental tracking receipt')
    validate_overflow(log)
    snapshots = collect(prior.parent, log)
    check_post_antenna_command(config, raw)
    path = Path('src/config_native_incremental_route_control.json')
    path.write_text(json.dumps(config, indent=2)+'\n')
    timing = OUTPUT/'timing'
    screen(path, raw, timing, os.environ['PDK_ROOT'], repaired=raw,
           sdc=Path('src/signoff.sdc'),
           extra_tcl=Path('workflow-src/scripts/ci/native_no_final_grt_audit.tcl'))
    audited = audit_post_antenna(prior, raw, timing)
    run_step(config, audited, OUTPUT/'antenna', ['OpenROAD.CheckAntennas'])
    antenna = json.loads(unique(OUTPUT/'antenna', '*-openroad-checkantennas/or_metrics_out.json').read_text())
    reports = {c: unique(timing/f'after-{c}', '*-openroad-stamidpnr/checks.rpt').read_text() for c in CORNERS}
    margin = measure(list(timing.glob('after-*/*-openroad-stamidpnr/electrical_margin.rpt')))
    gates = evaluate(json.loads((timing/'comparison.json').read_text()), antenna, reports, margin)
    gates = record_capture(gates, timing)
    gates = record_control_image(gates, image)
    coverage = {c: routing_objects(unique(timing/f'after-{c}',
                '*-openroad-stamidpnr/route_coverage.rpt').read_text(), c) for c in CORNERS}
    if any(v != coverage[CORNERS[0]] for v in coverage.values()):
        raise ValueError('Corner route coverage disagrees on the same physical database')
    gates.update(source_run=PROFILE['source_run'], source_sha=PROFILE['source_sha'],
                 source_stage=SOURCE_STAGE, source_odb_sha256=SOURCE_ODB_HASH,
                 final_full_reroute=False, incremental_reroute=True, snapshots=snapshots,
                 final_state=str(audited),
                 routing_object_counts=coverage, routing_completeness_proven=False,
                 all_signal_nets_have_routing_objects=coverage[CORNERS[0]]['MISSING_NETS'] == 0)
    gates['checkpoint_measured_gates_pass'] &= gates['all_signal_nets_have_routing_objects']
    if digest(source_odb) != SOURCE_ODB_HASH:
        raise ValueError('Control mutated original physical database')
    (OUTPUT/'gates.json').write_text(json.dumps(gates, indent=2)+'\n')
    print(json.dumps(gates, indent=2), flush=True)


if __name__ == '__main__':
    main()

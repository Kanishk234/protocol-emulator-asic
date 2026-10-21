"""Checkpoint-only control of the native final full-reroute switch; never signoff."""
import json
import os
from pathlib import Path
import re

from electrical_margin_gate import measure
from event_nor2_screen import validate_overflow
from native_lane_mask_stage_probe import PROFILE
from native_margin_screen import audit_post_antenna, check_post_antenna_command, evaluate
from native_setup_reserve_screen import MINIMUM_SLOW_CAPTURE_SETUP_NS, capture_setup
from native_stage_probe import digest, validate
from native_stock_route import run_step
from postgrt_timing import CORNERS, screen
from sram_bank_clean_route import unique

SOURCE_STAGE = '43-openroad-repairantennas'
SOURCE_ODB_HASH = '96d32d5a1b7a6d0ba0d6acfd7c2222b68f3285dde814f86c31acf68a22e2a4cf'
OUTPUT = Path('runs/native-no-final-grt-control')


def configure(original):
    expected = dict(CLOCK_PERIOD=20, PL_TARGET_DENSITY_PCT=56, SYNTH_STRATEGY='AREA 1',
                    GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH=150,
                    GRT_DESIGN_REPAIR_MAX_SLEW_PCT=55, GRT_DESIGN_REPAIR_MAX_CAP_PCT=55,
                    GRT_RESIZER_HOLD_SLACK_MARGIN=.125, GRT_RESIZER_SETUP_SLACK_MARGIN=0,
                    GRT_ALLOW_CONGESTION=False, GRT_ANTENNA_REPAIR_MARGIN=50,
                    PNR_CORNERS=list(CORNERS), RSZ_CORNERS=list(CORNERS))
    if any(original.get(k) != v for k, v in expected.items()):
        raise ValueError('Wrong no-final-GRT control source policy')
    # Pinned LibreLane defaults this option True, omitted from input configs.
    if original.get('GRT_RESIZER_RUN_GRT', True) is not True:
        raise ValueError('Source must use the native final full reroute')
    for key in ('PNR_SDC_FILE', 'SIGNOFF_SDC_FILE'):
        if Path(original.get(key, '')).resolve() != Path('src/signoff.sdc').resolve():
            raise ValueError('Wrong fully timed control constraints')
    return dict(original, GRT_RESIZER_RUN_GRT=False)


def record_capture(gates, timing):
    measured = {c: capture_setup(unique(timing/f'after-{c}',
                    '*-openroad-stamidpnr/capture_setup.rpt').read_text()) for c in CORNERS}
    setup_pass = measured[CORNERS[1]] >= MINIMUM_SLOW_CAPTURE_SETUP_NS
    # Measurement success is distinct from design qualification. Even a control
    # passing every measurement still needs routing/clean-build reproduction.
    return dict(gates, qualified=False, diagnostic_only=True, route_authorized=False,
                clean_synthesis=False, checkpoint_continuation=True, reproduction_required=True,
                official_signoff=False, physical_gate_checks_complete=True,
                minimum_slow_capture_setup_ns=MINIMUM_SLOW_CAPTURE_SETUP_NS,
                capture_setup_minimum_ns=measured, estimated_setup_reserve_pass=setup_pass,
                checkpoint_measured_gates_pass=bool(gates['qualified'] and setup_pass))


def routing_objects(report, corner):
    if (report.count(f'TRIPWIRE_ROUTE_COVERAGE_BEGIN {corner}\n') != 1
            or report.count('TRIPWIRE_ROUTE_COVERAGE_END\n') != 1):
        raise ValueError('Missing control route coverage markers')
    counts = {}
    for key in ('SIGNAL_NETS', 'GUIDE_NETS', 'WIRE_ONLY_NETS', 'MISSING_NETS'):
        matches = re.findall(r'^'+key+r' (\d+)$', report, re.M)
        if len(matches) != 1:
            raise ValueError('Missing unique control route count')
        counts[key] = int(matches[0])
    if (counts['SIGNAL_NETS'] <= 0 or counts['SIGNAL_NETS'] != sum(
            counts[k] for k in ('GUIDE_NETS', 'WIRE_ONLY_NETS', 'MISSING_NETS'))
            or len(re.findall(r'^MISSING_NET_HEX [0-9a-f]+$', report, re.M)) != counts['MISSING_NETS']):
        raise ValueError('Inconsistent control route counts')
    return counts


def main():
    original = json.loads(Path('src/config_native_stock.json').read_text())
    validate(json.loads(Path('/tmp/native-source-run.json').read_text()), original, PROFILE)
    config = configure(original)
    source = Path('runs/native-stock-screen/flow')/SOURCE_STAGE/'state_out.json'
    source_odb = Path(json.loads(source.read_text())['odb'])
    if (source_odb.name != 'tt_um_tripwire.odb'
            or not source_odb.resolve().is_relative_to(source.parent.resolve())
            or digest(source_odb) != SOURCE_ODB_HASH):
        raise ValueError('Wrong exact pre-hold control database')
    OUTPUT.mkdir(exist_ok=False)
    os.environ.pop('LIBRELANE_IMAGE_OVERRIDE', None)
    run_step(config, source, OUTPUT/'flow',
             ['OpenROAD.ResizerTimingPostGRT', 'OpenROAD.RepairAntennas'])
    prior = unique(OUTPUT/'flow', '*-openroad-resizertimingpostgrt/state_out.json')
    raw = unique(OUTPUT/'flow', '*-openroad-repairantennas/state_out.json')
    validate_overflow((prior.parent/'openroad-resizertimingpostgrt.log').read_text())
    check_post_antenna_command(config, raw)
    path = Path('src/config_native_no_final_grt_control.json')
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
    coverage = {c: routing_objects(unique(timing/f'after-{c}',
                '*-openroad-stamidpnr/route_coverage.rpt').read_text(), c) for c in CORNERS}
    if any(v != coverage[CORNERS[0]] for v in coverage.values()):
        raise ValueError('Corner route coverage disagrees on the same physical database')
    gates.update(source_run=PROFILE['source_run'], source_sha=PROFILE['source_sha'],
                 source_stage=SOURCE_STAGE, source_odb_sha256=SOURCE_ODB_HASH,
                 final_full_reroute=False, final_state=str(audited),
                 routing_object_counts=coverage, routing_completeness_proven=False,
                 all_signal_nets_have_routing_objects=coverage[CORNERS[0]]['MISSING_NETS'] == 0)
    gates['checkpoint_measured_gates_pass'] &= gates['all_signal_nets_have_routing_objects']
    if digest(source_odb) != SOURCE_ODB_HASH:
        raise ValueError('Control mutated original physical database')
    (OUTPUT/'gates.json').write_text(json.dumps(gates, indent=2)+'\n')
    print(json.dumps(gates, indent=2), flush=True)


if __name__ == '__main__':
    main()

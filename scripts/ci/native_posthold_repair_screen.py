"""Measure one native electrical repair after hold; no route authorization."""
import json
import os
from pathlib import Path

from electrical_margin_gate import measure
from event_nor2_screen import validate_overflow
from native_margin_screen import audit_post_antenna, check_post_antenna_command, evaluate
from native_setup_reserve_screen import enforce
from native_stage_probe import digest, validate
from native_stock_route import run_step
from postgrt_timing import CORNERS, screen
from sram_bank_clean_route import unique


def configure(original):
    expected = dict(GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH=150,
        GRT_DESIGN_REPAIR_MAX_SLEW_PCT=55, GRT_DESIGN_REPAIR_MAX_CAP_PCT=55,
        GRT_RESIZER_HOLD_SLACK_MARGIN=.125, GRT_RESIZER_SETUP_SLACK_MARGIN=0,
        GRT_DESIGN_REPAIR_RUN_GRT=True, GRT_ALLOW_CONGESTION=False)
    if any(original.get(k) != v for k, v in expected.items()):
        raise ValueError('Wrong post-hold repair source policy')
    # Physical repair targets only: the measured 0.45 reserve limit stays fixed.
    return dict(original, GRT_DESIGN_REPAIR_MAX_SLEW_PCT=60,
                GRT_DESIGN_REPAIR_MAX_CAP_PCT=60)


def main():
    original = json.loads(Path('src/config_native_stock.json').read_text())
    validate(json.loads(Path('/tmp/native-source-run.json').read_text()), original)
    config = configure(original)
    source = Path('runs/native-stock-screen/flow/44-openroad-resizertimingpostgrt/state_out.json')
    source_odb = Path(json.loads(source.read_text())['odb'])
    if source_odb.resolve() != (source.parent/'tt_um_tripwire.odb').resolve():
        raise ValueError('Wrong post-hold database')
    before = digest(source_odb)
    root = Path('runs/native-posthold-margin60'); root.mkdir(exist_ok=False)
    os.environ.pop('LIBRELANE_IMAGE_OVERRIDE', None)
    # No synthesis or timing repair is repeated; exact native repair then antenna.
    run_step(config, source, root/'flow', ['OpenROAD.RepairDesignPostGRT', 'OpenROAD.RepairAntennas'])
    prior = unique(root/'flow', '*-openroad-repairdesignpostgrt/state_out.json')
    raw = unique(root/'flow', '*-openroad-repairantennas/state_out.json')
    validate_overflow((prior.parent/'openroad-repairdesignpostgrt.log').read_text())
    check_post_antenna_command(config, raw)
    path = Path('src/config_native_posthold_margin60.json')
    path.write_text(json.dumps(config, indent=2)+'\n')
    timing = root/'timing'
    screen(path, raw, timing, os.environ['PDK_ROOT'], repaired=raw,
           sdc=Path('src/signoff.sdc'),
           extra_tcl=Path('workflow-src/scripts/ci/native_timing_headroom_audit.tcl'))
    audited = audit_post_antenna(prior, raw, timing)
    run_step(config, audited, root/'antenna', ['OpenROAD.CheckAntennas'])
    antenna = json.loads(unique(root/'antenna', '*-openroad-checkantennas/or_metrics_out.json').read_text())
    reports = {c: unique(timing/f'after-{c}', '*-openroad-stamidpnr/checks.rpt').read_text() for c in CORNERS}
    margin = measure(list(timing.glob('after-*/*-openroad-stamidpnr/electrical_margin.rpt')))
    gates = evaluate(json.loads((timing/'comparison.json').read_text()), antenna, reports, margin)
    gates.update(source_run=39468700509, clean_synthesis=False, checkpoint_continuation=True,
                 reproduction_required=True, route_authorized=False,
                 final_state=str(audited), source_native_electrical_margin_pct=55,
                 native_electrical_margin_pct=60, posthold_electrical_margin_pct=60)
    (root/'gates.json').write_text(json.dumps(gates, indent=2)+'\n')
    if digest(source_odb) != before:
        raise ValueError('Source database changed')
    # Parse setup reserve even if electrical fails, preserving both diagnoses.
    enforce(root)
    gates = json.loads((root/'gates.json').read_text())
    gates.update(checkpoint_physical_gates_pass=gates['qualified'], qualified=False)
    (root/'gates.json').write_text(json.dumps(gates, indent=2)+'\n')


if __name__ == '__main__':
    main()

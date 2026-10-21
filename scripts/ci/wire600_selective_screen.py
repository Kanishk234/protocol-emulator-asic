"""Source-bound checkpoint experiment; passing measurements require clean replay."""
import json
import os
from pathlib import Path
import subprocess

from electrical_margin_gate import measure
from electrical_repair_plan import validate_change
from event_nor2_screen import logical_cells, validate_overflow
from native_margin_screen import audit_post_antenna, check_post_antenna_command, evaluate
from native_no_final_grt_control import record_capture, routing_objects
from native_stock_route import run_step
from postgrt_timing import CORNERS, screen
from sram_bank_clean_route import unique
from sram_bank_plan import MACRO_LEF_SHA
from wire600_selective_plan import BINDING, digest, plan, target_call, validate_files

OUTPUT = Path('runs/wire600-selective-screen')


def validate_run(run):
    if any(run.get(k) != v for k, v in {
        'id': BINDING['source_run'], 'head_sha': BINDING['source_head'],
        'head_branch': 'main', 'path': BINDING['source_path'], 'conclusion': 'failure',
    }.items()):
        raise ValueError('Wrong selective checkpoint provenance')


def main():
    validate_run(json.loads(Path('/tmp/native-source-run.json').read_text()))
    validate_files(Path.cwd())
    files = BINDING['files']
    source = Path(BINDING['source_state'])
    state = json.loads(source.read_text())
    for key in ('odb', 'nl', 'def'):
        if Path(state[key]).resolve() != Path(files[key]['path']).resolve():
            raise ValueError('Selective state points outside bound source')
    macro = [p for p in Path('macro').rglob('*.lef') if digest(p) == MACRO_LEF_SHA]
    if len(macro) != 1:
        raise ValueError('Missing pinned SRAM geometry')
    proposal = plan(Path.cwd(), macro[0])
    target = Path('workflow-src/scripts/ci/wire600_selective_targets.tcl')
    if target.exists():
        raise ValueError('Repeated selective target generation')
    target.write_text(target_call(Path(files['def']['path']).read_text(), proposal))
    OUTPUT.mkdir(exist_ok=False)
    (OUTPUT/'proposal.json').write_text(json.dumps(proposal, indent=2)+'\n')
    image = 'tripwire-wire600-selective:local'
    subprocess.run(['docker', 'build', '-t', image, '-f',
                    'workflow-src/scripts/ci/Dockerfile.openroad-wire600-selective',
                    'workflow-src/scripts/ci'], check=True)
    os.environ['LIBRELANE_IMAGE_OVERRIDE'] = image
    config = json.loads(Path(files['config']['path']).read_text())
    # Discard metrics/derived views from the source; retain physical source files.
    initial = OUTPUT/'source_state.json'
    initial.write_text(json.dumps(dict(state, metrics={}, spef=None, sdf=None, lib=None), indent=2)+'\n')
    run_step(config, initial, OUTPUT/'flow',
             ['OpenROAD.ResizerTimingPostGRT', 'OpenROAD.RepairAntennas'])
    prior = unique(OUTPUT/'flow', '*-openroad-resizertimingpostgrt/state_out.json')
    raw = unique(OUTPUT/'flow', '*-openroad-repairantennas/state_out.json')
    before = (prior.parent/'selective.before.v').read_text()
    after = (prior.parent/'selective.after.v').read_text()
    if logical_cells(before) != logical_cells(Path(files['nl']['path']).read_text()):
        raise ValueError('Selective input netlist disagrees with exact source')
    validate_change(before, after, proposal)
    log = (prior.parent/'openroad-resizertimingpostgrt.log').read_text()
    if log.count('TRIPWIRE_SELECTIVE repaired and refreshed; native timing repair follows') != 1:
        raise ValueError('Missing selective repair execution receipt')
    if any(log.count('TRIPWIRE_INCREMENTAL '+m+'\n') != 1 for m in ('begin', 'end')):
        raise ValueError('Missing native incremental routing execution')
    validate_overflow(log)
    check_post_antenna_command(config, raw)
    cfg = OUTPUT/'config.json'
    cfg.write_text(json.dumps(config, indent=2)+'\n')
    timing = OUTPUT/'timing'
    screen(cfg, raw, timing, os.environ['PDK_ROOT'], repaired=raw,
           sdc=Path('src/signoff.sdc'),
           extra_tcl=Path('workflow-src/scripts/ci/native_no_final_grt_audit.tcl'))
    audited = audit_post_antenna(prior, raw, timing)
    run_step(config, audited, OUTPUT/'antenna', ['OpenROAD.CheckAntennas'])
    antenna = json.loads(unique(OUTPUT/'antenna', '*-openroad-checkantennas/or_metrics_out.json').read_text())
    reports = {c: unique(timing/f'after-{c}', '*-openroad-stamidpnr/checks.rpt').read_text() for c in CORNERS}
    margins = measure(list(timing.glob('after-*/*-openroad-stamidpnr/electrical_margin.rpt')))
    gates = record_capture(evaluate(json.loads((timing/'comparison.json').read_text()), antenna, reports, margins), timing)
    coverage = {c: routing_objects(unique(timing/f'after-{c}', '*-openroad-stamidpnr/route_coverage.rpt').read_text(), c) for c in CORNERS}
    if any(v != coverage[CORNERS[0]] for v in coverage.values()):
        raise ValueError('Selective route coverage differs across corners')
    covered = coverage[CORNERS[0]]['MISSING_NETS'] == 0
    gates.update(source_run=BINDING['source_run'], identity_connectivity_audited=True,
                 custom_image=True, custom_image_name=image, native_routing_modified=True,
                 selective_buffers=proposal['buffers'], selective_targets=proposal['target_count'],
                 final_state=str(audited), routing_object_counts=coverage,
                 all_signal_nets_have_routing_objects=covered, routing_completeness_proven=False,
                 checkpoint_measured_gates_pass=gates['checkpoint_measured_gates_pass'] and covered)
    validate_files(Path.cwd())
    (OUTPUT/'gates.json').write_text(json.dumps(gates, indent=2)+'\n')
    print(json.dumps(gates, indent=2), flush=True)
    if not gates['checkpoint_measured_gates_pass']:
        raise ValueError('Selective electrical checkpoint fails strict gates; no routing')


if __name__ == '__main__':
    main()

"""Route only the exact repaired checkpoint reproduced from fresh RTL synthesis."""
import json
import os
from pathlib import Path

from electrical_incremental_route import continue_route
from event_nor2_screen import logical_cells, validate_overflow
from native_margin_screen import audit_post_antenna, check_post_antenna_command
from native_no_final_grt_control import record_capture, routing_objects
from native_post_antenna_route import evaluate_saved
from native_stock_route import run_step
from postgrt_timing import CORNERS, screen
from sram_bank_clean_route import unique
from wire600_reserve_last import REVIEW, validate_change
from wire600_reserve_finish import validate_proposal
from wire600_selective_plan import BINDING, digest, validate_files

REVIEW_PATH = Path(__file__).parent/'fixtures/wire600_selective/clean_route.json'
ROOT = Path('runs/wire600-clean-reproduction')
OUTPUT = Path('runs/wire600-clean-route')


def review():
    return json.loads(REVIEW_PATH.read_text())


def validate_bundle(root, run, *, bound=None, screen_root=ROOT):
    root = Path(root)
    bound = review() if bound is None else bound
    if any(run.get(k) != v for k, v in bound['run_binding'].items()):
        raise ValueError('Wrong clean reproduction provenance')
    for name, sha in bound['files'].items():
        if digest(root/name) != sha:
            raise ValueError('Changed clean reproduction file: '+name)
    receipt = json.loads((root/Path(screen_root)/'reproduction.json').read_text())
    required = dict(clean_synthesis=True, source_artifact_downloaded=False,
                    exact_source_reproduced=True, repaired_measured_gates_pass=True,
                    official_signoff=False, qualified=False)
    if any(receipt.get(k) != v for k, v in required.items()):
        raise ValueError('Incomplete clean reproduction receipt')
    if receipt.get('final_state') != bound['source_state']:
        raise ValueError('Wrong reproduced physical state')
    return root/bound['source_state']


def measured_gates(root, timing, antenna):
    gates = record_capture(evaluate_saved(root, timing, antenna), timing)
    coverage = {c: routing_objects(unique(timing/f'after-{c}',
                    '*-openroad-stamidpnr/route_coverage.rpt').read_text(), c)
                for c in CORNERS}
    covered = (all(v == coverage[CORNERS[0]] for v in coverage.values())
               and coverage[CORNERS[0]]['MISSING_NETS'] == 0)
    gates.update(all_signal_nets_have_routing_objects=covered,
                 routing_object_counts=coverage,
                 checkpoint_measured_gates_pass=gates['checkpoint_measured_gates_pass'] and covered)
    if not gates['checkpoint_measured_gates_pass']:
        raise ValueError('Strict setup/hold/electrical/reserve/antenna/coverage gates fail; no DRT')
    return gates


def validate_checkpoint(*, bound=None, screen_root=ROOT, proposal_review=REVIEW,
                        connectivity_audit=validate_change):
    validate_files(Path.cwd())
    source = validate_bundle(Path.cwd(), json.loads(Path('/tmp/wire600-clean-source-run.json').read_text()),
                             bound=bound, screen_root=screen_root)
    repaired = Path(screen_root)/'repaired'
    proposal = json.loads((repaired/'proposal.json').read_text())
    validate_proposal(proposal, proposal_review)
    prior = unique(repaired/'flow', '*-openroad-resizertimingpostgrt/state_out.json')
    raw = unique(repaired/'flow', '*-openroad-repairantennas/state_out.json')
    before = (prior.parent/'selective.before.v').read_text()
    if logical_cells(before) != logical_cells(Path(BINDING['files']['nl']['path']).read_text()):
        raise ValueError('Wrong clean repair input topology')
    connectivity_audit(before, (prior.parent/'selective.after.v').read_text(), proposal)
    log = (prior.parent/'openroad-resizertimingpostgrt.log').read_text()
    validate_overflow(log)
    if any(log.count(marker+'\n') != 1 for marker in (
            'TRIPWIRE_INCREMENTAL begin', 'TRIPWIRE_INCREMENTAL end',
            'TRIPWIRE_SELECTIVE repaired and refreshed; native timing repair follows')):
        raise ValueError('Missing unique clean repair execution')
    config = json.loads(Path(BINDING['files']['config']['path']).read_text())
    check_post_antenna_command(config, raw)
    timing = repaired/'timing'
    if Path(json.loads((timing/'comparison.json').read_text())['after_state']).resolve() != raw.resolve():
        raise ValueError('Saved timing reads a different antenna state')
    saved = source.read_bytes()
    audited = audit_post_antenna(prior, raw, timing)
    if audited.resolve() != source.resolve() or audited.read_bytes() != saved:
        raise ValueError('Clean readback audit changed saved state')
    antenna = json.loads(unique(repaired/'antenna', '*-openroad-checkantennas/or_metrics_out.json').read_text())
    measured_gates(repaired, timing, antenna)
    return config, source


def main(profile=None):
    if profile is None:
        config, source = validate_checkpoint()
        bound, screen_root, output = review(), ROOT, OUTPUT
    else:
        bound, screen_root, output = profile['binding'], profile['screen_root'], Path(profile['output'])
        config, source = validate_checkpoint(bound=bound, screen_root=screen_root,
            proposal_review=profile['proposal_review'], connectivity_audit=profile['connectivity_audit'])
    output.mkdir(exist_ok=False)
    os.environ.pop('LIBRELANE_IMAGE_OVERRIDE', None)
    run_step(config, source, output/'antenna', ['OpenROAD.CheckAntennas'])
    cfg = Path('src/config_'+output.name.replace('-', '_')+'.json')
    cfg.write_text(json.dumps(config, indent=2)+'\n')
    screen(cfg, source, output/'timing', os.environ['PDK_ROOT'], repaired=source,
           sdc=Path('src/signoff.sdc'),
           extra_tcl=Path('workflow-src/scripts/ci/native_no_final_grt_audit.tcl'))
    antenna = json.loads(unique(output/'antenna', '*-openroad-checkantennas/or_metrics_out.json').read_text())
    fresh = measured_gates(output, output/'timing', antenna)
    fresh.update(clean_preparation_reproduced=True, repair_repeated=False,
                 source_run=bound['run_binding']['id'], drt_preparation_pass=True)
    (output/'preparation_gates.json').write_text(json.dumps(fresh, indent=2)+'\n')
    continue_route(config, source, output/'qualified-route', source_run=bound['run_binding']['id'])
    validate_bundle(Path.cwd(), json.loads(Path('/tmp/wire600-clean-source-run.json').read_text()),
                    bound=bound, screen_root=screen_root)


if __name__ == '__main__':
    main()

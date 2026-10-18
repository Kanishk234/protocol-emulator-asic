"""Route only the exact all-gates-passing clean native antenna checkpoint."""
import argparse
import json
import os
from pathlib import Path

from electrical_margin_gate import measure
from event_nor2_screen import validate_overflow
from native_margin_screen import audit_post_antenna, check_post_antenna_command, evaluate
from native_post_antenna_screen import configure as final_configure
from native_stock_route import fingerprints, run_step
from native_stock_screen import checkpoint, configure
from postgrt_timing import CORNERS, screen
from sram_bank_clean_route import unique

SOURCE_RUN = 39141162581
SOURCE_SHA = '8dbebcc76aea4f2c47875a521e24c1eacf951bb6'
ROOT = Path('runs/native-stock-screen')
OUTPUT = Path('runs/native-post-timing-antenna-route')


def prepare():
    expected = configure(json.loads(Path('src/config_merged.json').read_text()),
                         'AREA 1', Path('src/signoff.sdc'), hold_target=.10, clock_cluster=8)
    Path('/tmp/native-trusted-config.json').write_text(json.dumps(final_configure(expected)))
    Path('/tmp/native-trusted-files.json').write_text(json.dumps(fingerprints(Path.cwd())))


def validate_provenance(run, gates, recipe):
    expected = dict(id=SOURCE_RUN, head_sha=SOURCE_SHA, head_branch='main', conclusion='success',
                    path='.github/workflows/gds-native-post-timing-antenna-screen.yaml')
    if any(run.get(k) != v for k, v in expected.items()):
        raise ValueError('Wrong qualified native antenna source')
    required = dict(qualified=True, minimum_fast_hold_ns=.05, clean_synthesis=True,
                    checkpoint_ecos=False, custom_image=False, physical_screen_only=True,
                    official_signoff=False, final_native_antenna_repair=True, stock_sequence=False,
                    estimated_margin_pass=True, estimated_margin_limit=.45)
    if any(gates.get(k) != v for k, v in required.items()):
        raise ValueError('Unqualified native antenna gate receipt')
    required = dict(source_variant='bs-event-late', synthesis_strategy='AREA 1',
                    stock_sequence=False, stock_prefix_sequence=True, checkpoint_ecos=False,
                    post_grt_design_repair=True, hold_target_ns=.10, clock_sink_clustering_size=8,
                    repair_corners=list(CORNERS), extra_native_steps=['OpenROAD.RepairAntennas'])
    if any(recipe.get(k) != v for k, v in required.items()):
        raise ValueError('Wrong native antenna recipe')


def evaluate_saved(root, timing_root, antenna):
    reports = {c: unique(timing_root/f'after-{c}', '*-openroad-stamidpnr/checks.rpt').read_text()
               for c in CORNERS}
    margin = measure(list(timing_root.glob('after-*/*-openroad-stamidpnr/electrical_margin.rpt')))
    return evaluate(json.loads((timing_root/'comparison.json').read_text()), antenna, reports, margin)


def validate_checkpoint(config, gates, recipe):
    if list(ROOT.rglob('*-openroad-detailedrouting')):
        raise ValueError('Screen unexpectedly contains detailed routing')
    raw = checkpoint(ROOT/'flow', final_antenna=True)
    prior = checkpoint(ROOT/'flow')
    validate_overflow((prior.parent/'openroad-resizertimingpostgrt.log').read_text())
    check_post_antenna_command(config, raw)
    timing_root = ROOT/'timing'
    timing = json.loads((timing_root/'comparison.json').read_text())
    if Path(timing['after_state']).resolve() != raw.resolve():
        raise ValueError('Saved timing measures wrong native antenna state')
    expected = raw.with_name('audited_state.json')
    for receipt in (gates, recipe):
        if (Path(receipt['final_state']).resolve() != expected.resolve()
                or Path(receipt['final_timing_root']).resolve() != timing_root.resolve()):
            raise ValueError('Wrong final native antenna receipt state')
    saved = json.loads(expected.read_text())
    source = audit_post_antenna(prior, raw, timing_root)
    if saved != json.loads(source.read_text()):
        raise ValueError('Saved audited state differs from independent readback audit')
    antenna = json.loads(unique(ROOT/'antenna', '*-openroad-checkantennas/or_metrics_out.json').read_text())
    measured = evaluate_saved(ROOT, timing_root, antenna)
    if not measured['qualified'] or any(gates.get(k) != v for k, v in measured.items()):
        raise ValueError('Saved native antenna gates differ from measured evidence')
    return source


def main():
    config = json.loads(Path('src/config_native_stock.json').read_text())
    if config != json.loads(Path('/tmp/native-trusted-config.json').read_text()):
        raise ValueError('Wrong full native antenna physical config')
    trusted = json.loads(Path('/tmp/native-trusted-files.json').read_text())
    actual = fingerprints(Path.cwd())
    def hardware(values):
        return {k: v for k, v in values.items()
                if not (k.startswith('src/config') and k.endswith('.json'))}
    if hardware(trusted) != hardware(actual):
        raise ValueError('Native antenna hardware/constraints fingerprint mismatch')
    gates = json.loads((ROOT/'gates.json').read_text())
    recipe = json.loads((ROOT/'recipe.json').read_text())
    validate_provenance(json.loads(Path('/tmp/native-source-run.json').read_text()), gates, recipe)
    source = validate_checkpoint(config, gates, recipe)
    OUTPUT.mkdir(exist_ok=False)
    os.environ.pop('LIBRELANE_IMAGE_OVERRIDE', None)
    # Fresh checks retain the strict reserve gate before DRT; no repair is repeated.
    run_step(config, source, OUTPUT/'antenna', ['OpenROAD.CheckAntennas'])
    path = Path('src/config_native_post_antenna_route.json')
    path.write_text(json.dumps(config, indent=2)+'\n')
    screen(path, source, OUTPUT/'timing', os.environ['PDK_ROOT'], repaired=source,
           sdc=Path('src/signoff.sdc'),
           extra_tcl=Path('workflow-src/scripts/ci/electrical_margin_probe.tcl'))
    antenna = json.loads(unique(OUTPUT/'antenna', '*-openroad-checkantennas/or_metrics_out.json').read_text())
    fresh = evaluate_saved(OUTPUT, OUTPUT/'timing', antenna)
    fresh.update(source_run=SOURCE_RUN, repair_repeated=False, state=str(source))
    (OUTPUT/'gates.json').write_text(json.dumps(fresh, indent=2)+'\n')
    if not fresh['qualified']:
        raise ValueError('Fresh native antenna gates fail; detailed routing refused')
    # Shared continuation audits DRT connectivity/zero DRC, extracts all corners,
    # and rejects negative setup, fast hold below 50ps, electrical or antenna errors.
    from electrical_incremental_route import continue_route
    continue_route(config, source, OUTPUT/'qualified-route', source_run=SOURCE_RUN)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    args = parser.parse_args()
    prepare() if args.prepare else main()

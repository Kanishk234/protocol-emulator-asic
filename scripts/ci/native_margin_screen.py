"""Clean native electrical-margin reproduction trial; no checkpoint ECOs or DRT."""
import json
from pathlib import Path

from electrical_margin_gate import measure
from electrical_report import audit
from event_nor2_screen import validate_overflow
from native_stock_route import qualified, run_step
from native_stock_screen import checkpoint, main as stock_screen
from postgrt_timing import CORNERS


def configure(config):
    expected = dict(CLOCK_PERIOD=20, PL_TARGET_DENSITY_PCT=56,
                    SYNTH_STRATEGY='AREA 1', CTS_SINK_CLUSTERING_SIZE=8,
                    GRT_RESIZER_HOLD_SLACK_MARGIN=.10,
                    RSZ_CORNERS=list(CORNERS), PNR_CORNERS=list(CORNERS))
    if any(config.get(k) != v for k, v in expected.items()):
        raise ValueError('Wrong clean clock8 source recipe')
    # Native repair targets reserve 55% of the limit. These do not relax
    # signoff constraints, nor guarantee that the final measured margin passes.
    return dict(config, RUN_POST_GRT_DESIGN_REPAIR=True,
                GRT_DESIGN_REPAIR_MAX_SLEW_PCT=55,
                GRT_DESIGN_REPAIR_MAX_CAP_PCT=55,
                GRT_ALLOW_CONGESTION=False,
                ERROR_ON_MAGIC_DRC=True, ERROR_ON_ILLEGAL_OVERLAPS=True)


def evaluate(timing, antenna, reports, margin):
    electrical = {c: audit(reports[c]) for c in CORNERS}
    ready = (qualified(timing, antenna)
             and all(row['no_reported_electrical_violations'] for row in electrical.values())
             and margin['estimated_margin_pass'] is True)
    return dict(qualified=ready, minimum_fast_hold_ns=.05,
                native_electrical_margin_pct=55, electrical=electrical,
                **margin, checkpoint_ecos=False, custom_image=False,
                clean_synthesis=True, physical_screen_only=True,
                official_signoff=False)


def main(config_transform=configure):
    stock_screen(config_transform=config_transform,
                 extra_tcl=Path('workflow-src/scripts/ci/electrical_margin_probe.tcl'))
    root = Path('runs/native-stock-screen')
    source = checkpoint(root/'flow')
    # Validate the final native incremental GRT, not an earlier placement log.
    validate_overflow((source.parent/'openroad-resizertimingpostgrt.log').read_text())
    config = json.loads(Path('src/config_native_stock.json').read_text())
    run_step(config, source, root/'antenna', ['OpenROAD.CheckAntennas'])
    metrics = list((root/'antenna').glob('*-openroad-checkantennas/or_metrics_out.json'))
    if len(metrics) != 1:
        raise ValueError('Missing fresh antenna check')
    reports = {}
    for corner in CORNERS:
        paths = list((root/'timing'/f'after-{corner}').glob('*-openroad-stamidpnr/checks.rpt'))
        if len(paths) != 1:
            raise ValueError('Missing fresh electrical checks')
        reports[corner] = paths[0].read_text()
    margin = measure(list((root/'timing').glob('after-*/*-openroad-stamidpnr/electrical_margin.rpt')))
    receipt = evaluate(json.loads((root/'timing/comparison.json').read_text()),
                       json.loads(metrics[0].read_text()), reports, margin)
    (root/'gates.json').write_text(json.dumps(receipt, indent=2)+'\n')
    if not receipt['qualified']:
        raise ValueError('Native clean-build margin screen fails; no detailed routing')


if __name__ == '__main__':
    main()

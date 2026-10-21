"""Clean native electrical-margin reproduction trial; no checkpoint ECOs or DRT."""
import json
from pathlib import Path
import re

from electrical_margin_gate import measure
from electrical_report import audit
from event_nor2_screen import validate_overflow, validate_antenna_only_changes
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
                antenna=antenna,
                **margin, checkpoint_ecos=False, custom_image=False,
                clean_synthesis=True, physical_screen_only=True,
                official_signoff=False)


def check_post_antenna_command(config, source):
    """Audit the native pass inserted by the declarative Classic recipe."""
    if config.get('GRT_ALLOW_CONGESTION') is not False:
        raise ValueError('Final native repair must disallow congestion')
    logs = list(source.parent.glob('*-openroad-diodeinsertion/openroad-diodeinsertion.log'))
    if len(logs) != 1:
        raise ValueError('Missing unique final native antenna state/log')
    commands = re.findall(r'^\+ repair_antennas .+$', logs[0].read_text(), re.M)
    if len(commands) != 1 or '-allow_congestion' in commands[0]:
        raise ValueError('Missing or unsafe final native antenna command')


def audit_post_antenna(before_state, repaired_state, timing_root):
    """The native antenna step exports ODB/DEF only: audit actual ODB readback."""
    old = json.loads(before_state.read_text())
    state = json.loads(repaired_state.read_text())
    before = Path(old['nl']).read_text()
    exports = []
    for corner in CORNERS:
        stages = list((timing_root/f'after-{corner}').glob('*-openroad-stamidpnr'))
        if len(stages) != 1:
            raise ValueError('Missing unique final STA readback')
        stage = stages[0]
        actual = json.loads((stage/'state_in.json').read_text())
        if Path(actual['odb']).resolve() != Path(state['odb']).resolve():
            raise ValueError('Final STA read a different physical database')
        nl, pnl = stage/'native_antenna.nl.v', stage/'native_antenna.pnl.v'
        if not nl.is_file() or not pnl.is_file():
            raise ValueError('Missing fresh native antenna netlist exports')
        validate_antenna_only_changes(before, nl.read_text())
        exports.append((nl, pnl))
    if any(n.read_bytes() != exports[0][0].read_bytes()
           or p.read_bytes() != exports[0][1].read_bytes() for n, p in exports[1:]):
        raise ValueError('Corner readbacks disagree on physical connectivity')
    state.update(nl=str(exports[0][0].resolve()), pnl=str(exports[0][1].resolve()),
                 spef=None, sdf=None, lib=None, metrics={})
    path = repaired_state.with_name('audited_state.json')
    path.write_text(json.dumps(state, indent=2)+'\n')
    return path


def main(config_transform=configure, final_antenna_repair=False, audit_tcl=None, image_override=None):
    extra = {'stop_step': 'OpenROAD.RepairAntennas-1'} if final_antenna_repair else {}
    if image_override is not None:
        extra['image_override'] = image_override
    probe = 'native_post_antenna_audit.tcl' if final_antenna_repair else 'electrical_margin_probe.tcl'
    stock_screen(config_transform=config_transform,
                 extra_tcl=Path(audit_tcl) if audit_tcl is not None else Path('workflow-src/scripts/ci')/probe, **extra)
    root = Path('runs/native-stock-screen')
    before_antenna = checkpoint(root/'flow')
    source = checkpoint(root/'flow', final_antenna=True) if final_antenna_repair else before_antenna
    # Validate the final native incremental GRT, not an earlier placement log.
    validate_overflow((before_antenna.parent/'openroad-resizertimingpostgrt.log').read_text())
    config = json.loads(Path('src/config_native_stock.json').read_text())
    timing_root = root/'timing'
    if final_antenna_repair:
        check_post_antenna_command(config, source)
        source = audit_post_antenna(before_antenna, source, timing_root)
        recipe_path = root/'recipe.json'
        recipe = json.loads(recipe_path.read_text())
        recipe.update(stock_sequence=False, stock_prefix_sequence=True,
                      extra_native_steps=['OpenROAD.RepairAntennas'],
                      final_state=str(source), final_timing_root=str(timing_root))
        recipe_path.write_text(json.dumps(recipe, indent=2)+'\n')
    run_step(config, source, root/'antenna', ['OpenROAD.CheckAntennas'])
    metrics = list((root/'antenna').glob('*-openroad-checkantennas/or_metrics_out.json'))
    if len(metrics) != 1:
        raise ValueError('Missing fresh antenna check')
    reports = {}
    for corner in CORNERS:
        paths = list((timing_root/f'after-{corner}').glob('*-openroad-stamidpnr/checks.rpt'))
        if len(paths) != 1:
            raise ValueError('Missing fresh electrical checks')
        reports[corner] = paths[0].read_text()
    margin = measure(list(timing_root.glob('after-*/*-openroad-stamidpnr/electrical_margin.rpt')))
    receipt = evaluate(json.loads((timing_root/'comparison.json').read_text()),
                       json.loads(metrics[0].read_text()), reports, margin)
    receipt.update(final_state=str(source), final_timing_root=str(timing_root),
                   final_native_antenna_repair=final_antenna_repair,
                   stock_sequence=not final_antenna_repair and image_override is None,
                   custom_image=image_override is not None,
                   custom_image_name=image_override,
                   native_routing_modified=image_override is not None)
    (root/'gates.json').write_text(json.dumps(receipt, indent=2)+'\n')
    if not receipt['qualified']:
        raise ValueError('Native clean-build margin screen fails; no detailed routing')


if __name__ == '__main__':
    main()

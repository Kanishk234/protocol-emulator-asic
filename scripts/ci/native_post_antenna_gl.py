"""Prepare exact-route protocol replay; requires completed, independently reviewed bytes."""
import json
import re
from pathlib import Path
from electrical_report import audit_corners
from native_route_gl import validate_electrical
from native_stock_route import qualified
from postgrt_timing import CORNERS

ROUTE_RUN = 39149073496
ROUTE_SHA = '5867ea0688b4443a44f7e2d5851245cdfe0f33dc'


def validate(root, run, reviewed_netlist_sha, reviewed_recipe_sha, reviewed_step_config_sha):
    for value in (reviewed_netlist_sha, reviewed_recipe_sha, reviewed_step_config_sha):
        if not re.fullmatch(r'[0-9a-f]{64}', value or ''):
            raise ValueError('Independent netlist, recipe and step-config SHA256 reviews required')
    profile = dict(run_binding=dict(id=ROUTE_RUN, head_sha=ROUTE_SHA, head_branch='main',
        conclusion='success', path='.github/workflows/gds-native-post-timing-antenna-route.yaml'),
        route_name='native-post-timing-antenna-route/qualified-route', source_run=39141162581,
        hold_target_ns=.10, recipe_sha256=reviewed_recipe_sha,
        step_config_sha256=reviewed_step_config_sha)
    result = validate_electrical(root, run, reviewed_netlist_sha, profile=profile)
    recipe = json.loads((root/'src/config_electrical_incremental_route.json').read_text())
    original = json.loads((root/'src/config_native_stock.json').read_text())
    if recipe != original:
        raise ValueError('Routed recipe differs from qualified clean native config')
    expected = dict(CTS_SINK_CLUSTERING_SIZE=8, CTS_DISTANCE_BETWEEN_BUFFERS=100,
                    GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH=100, GRT_ANTENNA_REPAIR_MARGIN=50,
                    GRT_DESIGN_REPAIR_MAX_SLEW_PCT=55, GRT_DESIGN_REPAIR_MAX_CAP_PCT=55,
                    RUN_POST_GRT_DESIGN_REPAIR=True, ERROR_ON_MAGIC_DRC=True,
                    ERROR_ON_ILLEGAL_OVERLAPS=True)
    if (any(recipe.get(k) != v for k,v in expected.items())
            or recipe.get('meta', {}).get('substituting_steps') != {
                '+OpenROAD.ResizerTimingPostGRT': 'OpenROAD.RepairAntennas'}):
        raise ValueError('Wrong clean native antenna physical recipe')
    extracted = root/'runs/extracted-timing'
    stages = list(extracted.glob('*-openroad-stapostpnr'))
    antennas = list(extracted.glob('*-openroad-checkantennas/or_metrics_out.json'))
    if len(stages) != 1 or len(antennas) != 1:
        raise ValueError('Missing unique extracted timing/antenna evidence')
    electrical = audit_corners(stages[0], CORNERS)
    if not all(row['no_reported_electrical_violations'] for row in electrical.values()):
        raise ValueError('Native antenna extracted electrical evidence fails')
    summary = json.loads((extracted/'corner_summary.json').read_text())
    antenna = json.loads(antennas[0].read_text())
    if not qualified({'corners': {c: {'after': summary} for c in CORNERS}}, antenna):
        raise ValueError('Native antenna extracted timing/antenna evidence fails')
    return result

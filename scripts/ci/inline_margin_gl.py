"""Bind protocol GL to the independently reviewed clean extracted inline route."""
import json
from pathlib import Path
from native_route_gl import validate_electrical
from postgrt_timing import CORNERS
from electrical_report import audit_corners
from native_stock_route import qualified

NETLIST_SHA='ac646d7424b75d53d61c5726dac5a83780753dd397e4b2b45c1a90b11ed8221d'
PROFILE={'run_binding': {'id': 38784492656,
                 'head_sha': '88850b1241a4d83609537602dc7d8c7857a9c3a8',
                 'head_branch': 'main',
                 'conclusion': 'success',
                 'path': '.github/workflows/gds-inline-margin-route.yaml'},
 'route_name': 'inline-margin-route',
 'source_run': 38777752196,
 'hold_target_ns': 0.125,
 'recipe_sha256': '2f9fdfe7d3d5922bd5d9da336c428549ecace376f13d1e73e039520ea6564d05',
 'step_config_sha256': '631edd16714a3a605df1ad6b0364a74987f0a01492edc02494f39030b2b1e3be'}


def validate(root,run,reviewed_netlist_sha):
    if reviewed_netlist_sha!=NETLIST_SHA:
        raise ValueError('Unreviewed clean inline routed netlist hash')
    result=validate_electrical(root,run,reviewed_netlist_sha,profile=PROFILE)
    extracted=root/'runs/extracted-timing'
    summary=json.loads((extracted/'corner_summary.json').read_text())
    stages=list(extracted.glob('*-openroad-stapostpnr'))
    antennas=list(extracted.glob('*-openroad-checkantennas/or_metrics_out.json'))
    if len(stages)!=1 or len(antennas)!=1:
        raise ValueError('Missing unique extracted timing/antenna evidence')
    electrical=audit_corners(stages[0],CORNERS)
    if not all(row['no_reported_electrical_violations'] for row in electrical.values()):
        raise ValueError('Clean inline electrical evidence fails')
    antenna=json.loads(antennas[0].read_text())
    if not qualified({'corners':{c:{'after':summary} for c in CORNERS}},antenna):
        raise ValueError('Clean inline extracted timing/antenna evidence fails')
    return result

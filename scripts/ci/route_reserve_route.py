"""Continue the exact reserve-qualified checkpoint through stock DRT and extraction."""
import json
from pathlib import Path
from combined_physical_route import main as route
from route_reserve_plan import plan, validate_change
from route_reserve_gate import measure
from post_antenna_fanout_audit import audit


def audit_with_reserve(before, after, root, log):
    result = audit(before, after, root, log)
    root = Path(root)
    layouts = list(root.glob('*.def'))
    if len(layouts) != 1:
        raise ValueError('Missing unique screened reserve layout')
    proposal = json.loads((root.parent.parent/'proposal.json').read_text())
    reserve = measure(layouts[0].read_text(), proposal)
    if not reserve['fanout_reserve_pass']:
        raise ValueError('Saved reserve no longer passes; no DRT')
    result.update(reserve)
    return result


PROFILE={'source_run': 38687129808, 'run_binding': {'id': 38687129808, 'head_sha': '682ba0d0c8cabc032eaa927f031e18baf4b31d96', 'head_branch': 'main', 'conclusion': 'success', 'path': '.github/workflows/gds-route-reserve-screen.yaml'}, 'gate_receipt': {'source_run': 38679335674, 'qualified': True, 'added_buffers': 19, 'resized_cells': 0, 'minimum_fast_hold_ns': 0.05, 'all_original_connections_audited': True, 'source_detailed_wires_cleared': True, 'full_reroute': True, 'custom_image': True, 'physical_screen_only': True, 'official_signoff': False, 'post_antenna_batches': 1, 'post_antenna_buffers': 3, 'maximum_post_antenna_buffers': 64, 'post_antenna_connectivity_audited': True, 'internal_maximum_loads': 6, 'loads': {'_04497_': 3, '_17287_': 3, '_17463_': 1, 'net7855': 3, 'net8798': 3, 'net8991': 3, 'tripwire_route_reserve_38679335674_0_net': 4, 'tripwire_route_reserve_38679335674_10_net': 4, 'tripwire_route_reserve_38679335674_11_net': 4, 'tripwire_route_reserve_38679335674_12_net': 1, 'tripwire_route_reserve_38679335674_13_net': 4, 'tripwire_route_reserve_38679335674_14_net': 4, 'tripwire_route_reserve_38679335674_15_net': 1, 'tripwire_route_reserve_38679335674_16_net': 4, 'tripwire_route_reserve_38679335674_17_net': 4, 'tripwire_route_reserve_38679335674_18_net': 1, 'tripwire_route_reserve_38679335674_1_net': 4, 'tripwire_route_reserve_38679335674_2_net': 1, 'tripwire_route_reserve_38679335674_3_net': 4, 'tripwire_route_reserve_38679335674_4_net': 4, 'tripwire_route_reserve_38679335674_5_net': 1, 'tripwire_route_reserve_38679335674_6_net': 2, 'tripwire_route_reserve_38679335674_7_net': 4, 'tripwire_route_reserve_38679335674_8_net': 4, 'tripwire_route_reserve_38679335674_9_net': 1, 'u_chip.g_lane[1].ot[9]': 3}, 'fanout_reserve_pass': True}, 'screen_root': 'runs/route-reserve-screen', 'recipe_path': 'src/config_route_reserve_screen.json', 'baseline_nl': 'runs/fanout-slew-route/drt/1-openroad-detailedrouting/tt_um_tripwire.nl.v', 'baseline_def': 'runs/fanout-slew-route/drt/1-openroad-detailedrouting/tt_um_tripwire.def', 'timing_root': 'runs/extracted-timing/11-openroad-stapostpnr', 'timing_corner_format': '{corner}', 'output_root': 'runs/route-reserve-route', 'saved_extraction_root': 'runs/route-reserve-source-extracted-timing'}
PROFILE.update(plan=plan, validate_change=validate_change, post_antenna_audit=audit_with_reserve)

if __name__ == '__main__':
    route(PROFILE)

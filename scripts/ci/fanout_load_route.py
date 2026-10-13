"""Exact qualified fanout/clock-diode screen continuation through stock DRT/extraction."""
from combined_physical_route import main as route
from fanout_load_plan import plan,validate_change
from post_antenna_fanout_audit import audit

PROFILE={'source_run': 38453218365, 'run_binding': {'id': 38453218365, 'head_sha': '57028198781956737a0709e16b88d18c7cd40d67', 'head_branch': 'main', 'conclusion': 'success', 'path': '.github/workflows/gds-fanout-load-screen.yaml'}, 'gate_receipt': {'source_run': 38433037592, 'qualified': True, 'added_buffers': 28, 'resized_cells': 0, 'minimum_fast_hold_ns': 0.05, 'all_original_connections_audited': True, 'source_detailed_wires_cleared': True, 'full_reroute': True, 'custom_image': True, 'physical_screen_only': True, 'official_signoff': False, 'post_antenna_batches': 0, 'post_antenna_buffers': 0, 'maximum_post_antenna_buffers': 64, 'post_antenna_connectivity_audited': True}, 'screen_root': 'runs/fanout-load-screen', 'recipe_path': 'src/config_fanout_load_screen.json', 'baseline_nl': 'runs/decode-combined-route/drt/1-openroad-detailedrouting/tt_um_tripwire.nl.v', 'baseline_def': 'runs/decode-combined-route/drt/1-openroad-detailedrouting/tt_um_tripwire.def', 'timing_root': 'runs/extracted-timing/11-openroad-stapostpnr', 'timing_corner_format': '{corner}', 'output_root': 'runs/fanout-load-route', 'saved_extraction_root': 'runs/fanout-load-source-extracted-timing'}
PROFILE.update(plan=plan,validate_change=validate_change,post_antenna_audit=audit)

if __name__=='__main__':route(PROFILE)

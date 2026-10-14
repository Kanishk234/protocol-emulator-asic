"""Exact qualified strength/fanout screen continuation through stock DRT/extraction."""
from combined_physical_route import main as route
from strength_fanout_plan import plan,validate_change
from post_antenna_fanout_audit import audit

PROFILE={'source_run': 38484835284, 'run_binding': {'id': 38484835284, 'head_sha': '4b4794ac554db70a90a18c590df9f0e1e193c1ac', 'head_branch': 'main', 'conclusion': 'success', 'path': '.github/workflows/gds-strength-fanout-screen.yaml'}, 'gate_receipt': {'source_run': 38456657314, 'qualified': True, 'added_buffers': 21, 'resized_cells': 4, 'minimum_fast_hold_ns': 0.05, 'all_original_connections_audited': True, 'source_detailed_wires_cleared': True, 'full_reroute': True, 'custom_image': True, 'physical_screen_only': True, 'official_signoff': False, 'post_antenna_batches': 1, 'post_antenna_buffers': 3, 'maximum_post_antenna_buffers': 64, 'post_antenna_connectivity_audited': True}, 'screen_root': 'runs/strength-fanout-screen', 'recipe_path': 'src/config_strength_fanout_screen.json', 'baseline_nl': 'runs/fanout-load-route/drt/1-openroad-detailedrouting/tt_um_tripwire.nl.v', 'baseline_def': 'runs/fanout-load-route/drt/1-openroad-detailedrouting/tt_um_tripwire.def', 'timing_root': 'runs/extracted-timing/11-openroad-stapostpnr', 'timing_corner_format': '{corner}', 'output_root': 'runs/strength-fanout-route', 'saved_extraction_root': 'runs/strength-fanout-source-extracted-timing'}
PROFILE.update(plan=plan,validate_change=validate_change,post_antenna_audit=audit)

if __name__=='__main__':route(PROFILE)

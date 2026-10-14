"""Exact qualified hold/electrical screen continuation through stock DRT/extraction."""
from combined_physical_route import main as route
from hold_electrical_plan import plan,validate_change
from post_antenna_fanout_audit import audit

PROFILE={'source_run': 38512982007, 'run_binding': {'id': 38512982007, 'head_sha': '888d467db8ff7858ab61928124c8cd2d5450942b', 'head_branch': 'main', 'conclusion': 'success', 'path': '.github/workflows/gds-hold-electrical-screen.yaml'}, 'gate_receipt': {'source_run': 38507730942, 'qualified': True, 'added_buffers': 143, 'resized_cells': 0, 'minimum_fast_hold_ns': 0.05, 'all_original_connections_audited': True, 'source_detailed_wires_cleared': True, 'full_reroute': True, 'custom_image': True, 'physical_screen_only': True, 'official_signoff': False, 'post_antenna_batches': 0, 'post_antenna_buffers': 0, 'maximum_post_antenna_buffers': 64, 'post_antenna_connectivity_audited': True}, 'screen_root': 'runs/hold-electrical-screen', 'recipe_path': 'src/config_hold_electrical_screen.json', 'baseline_nl': 'runs/strength-residual-route/drt/1-openroad-detailedrouting/tt_um_tripwire.nl.v', 'baseline_def': 'runs/strength-residual-route/drt/1-openroad-detailedrouting/tt_um_tripwire.def', 'timing_root': 'runs/extracted-timing/11-openroad-stapostpnr', 'timing_corner_format': '{corner}', 'output_root': 'runs/hold-electrical-route', 'saved_extraction_root': 'runs/hold-electrical-source-extracted-timing'}
PROFILE.update(plan=plan,validate_change=validate_change,post_antenna_audit=audit)

if __name__=='__main__':route(PROFILE)

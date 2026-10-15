"""Exact qualified fanout/slew screen continuation through stock DRT/extraction."""
from combined_physical_route import main as route
from fanout_slew_plan import plan,validate_change
from post_antenna_fanout_audit import audit

PROFILE={'source_run': 38676308492, 'run_binding': {'id': 38676308492, 'head_sha': '8e0802002278fea9c790ec26ba15077ab61325af', 'head_branch': 'main', 'conclusion': 'success', 'path': '.github/workflows/gds-fanout-slew-screen.yaml'}, 'gate_receipt': {'source_run': 38668749394, 'qualified': True, 'added_buffers': 8, 'resized_cells': 0, 'minimum_fast_hold_ns': 0.05, 'all_original_connections_audited': True, 'source_detailed_wires_cleared': True, 'full_reroute': True, 'custom_image': True, 'physical_screen_only': True, 'official_signoff': False, 'post_antenna_batches': 1, 'post_antenna_buffers': 3, 'maximum_post_antenna_buffers': 64, 'post_antenna_connectivity_audited': True}, 'screen_root': 'runs/fanout-slew-screen', 'recipe_path': 'src/config_fanout_slew_screen.json', 'baseline_nl': 'runs/fanout-finish-route/drt/1-openroad-detailedrouting/tt_um_tripwire.nl.v', 'baseline_def': 'runs/fanout-finish-route/drt/1-openroad-detailedrouting/tt_um_tripwire.def', 'timing_root': 'runs/extracted-timing/11-openroad-stapostpnr', 'timing_corner_format': '{corner}', 'output_root': 'runs/fanout-slew-route', 'saved_extraction_root': 'runs/fanout-slew-source-extracted-timing'}
PROFILE.update(plan=plan,validate_change=validate_change,post_antenna_audit=audit)

if __name__=='__main__':route(PROFILE)

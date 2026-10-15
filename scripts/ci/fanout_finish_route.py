"""Exact qualified two-net fanout screen continuation through stock DRT/extraction."""
from combined_physical_route import main as route
from fanout_finish_plan import plan,validate_change
from post_antenna_fanout_audit import audit

PROFILE={'source_run': 38652802189, 'run_binding': {'id': 38652802189, 'head_sha': '95695ed7e7813977a2134075f73b15a369e399a9', 'head_branch': 'main', 'conclusion': 'success', 'path': '.github/workflows/gds-fanout-finish-screen.yaml'}, 'gate_receipt': {'source_run': 38641675550, 'qualified': True, 'added_buffers': 7, 'resized_cells': 0, 'minimum_fast_hold_ns': 0.05, 'all_original_connections_audited': True, 'source_detailed_wires_cleared': True, 'full_reroute': True, 'custom_image': True, 'physical_screen_only': True, 'official_signoff': False, 'post_antenna_batches': 0, 'post_antenna_buffers': 0, 'maximum_post_antenna_buffers': 64, 'post_antenna_connectivity_audited': True}, 'screen_root': 'runs/fanout-finish-screen', 'recipe_path': 'src/config_fanout_finish_screen.json', 'baseline_nl': 'runs/sram-residual-route/drt/1-openroad-detailedrouting/tt_um_tripwire.nl.v', 'baseline_def': 'runs/sram-residual-route/drt/1-openroad-detailedrouting/tt_um_tripwire.def', 'timing_root': 'runs/extracted-timing/11-openroad-stapostpnr', 'timing_corner_format': '{corner}', 'output_root': 'runs/fanout-finish-route', 'saved_extraction_root': 'runs/fanout-finish-source-extracted-timing'}
PROFILE.update(plan=plan,validate_change=validate_change,post_antenna_audit=audit)

if __name__=='__main__':route(PROFILE)

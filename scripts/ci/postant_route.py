"""Exact qualified post-antenna screen continuation through stock DRT/extraction."""
from combined_physical_route import main as route
from postant_screen_plan import plan,validate_change
from post_antenna_fanout_audit import audit

PROFILE={'source_run': 38356513586, 'run_binding': {'id': 38356513586, 'head_sha': '5671a0d06461aad776cbdfd55c262644d3b26370', 'head_branch': 'main', 'conclusion': 'success', 'path': '.github/workflows/gds-postant-fanout-screen.yaml'}, 'gate_receipt': {'source_run': 38353731199, 'qualified': True, 'added_buffers': 8, 'resized_cells': 0, 'minimum_fast_hold_ns': 0.05, 'all_original_connections_audited': True, 'source_detailed_wires_cleared': False, 'full_reroute': True, 'custom_image': True, 'physical_screen_only': True, 'official_signoff': False, 'source_global_screen': True, 'source_detailed_wire_reset_count': 0, 'post_antenna_batches': 1, 'post_antenna_buffers': 3, 'maximum_post_antenna_buffers': 64, 'post_antenna_connectivity_audited': True}, 'screen_root': 'runs/postant-screen', 'recipe_path': 'src/config_postant_screen.json', 'baseline_nl': 'runs/screen-fanout-finish-v2/grt/1-openroad-globalrouting/tt_um_tripwire.eco.nl.v', 'baseline_def': 'runs/screen-fanout-finish-v2/grt/1-openroad-globalrouting/tt_um_tripwire.def', 'timing_root': 'runs/screen-fanout-finish-v2/timing', 'timing_corner_format': 'after-{corner}/1-openroad-stamidpnr', 'output_root': 'runs/postant-route', 'saved_extraction_root': 'runs/postant-source-extracted-timing'}
PROFILE.update(plan=plan,validate_change=validate_change,post_antenna_audit=audit)

if __name__=='__main__':route(PROFILE)

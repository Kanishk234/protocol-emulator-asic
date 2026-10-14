"""Exact qualified residual electrical screen continuation through stock DRT/extraction."""
from combined_physical_route import main as route
from strength_residual_plan import plan,validate_change
from post_antenna_fanout_audit import audit

PROFILE={'source_run': 38505802817, 'run_binding': {'id': 38505802817, 'head_sha': '1fb72d7074c71b73bdbde431a276879a4ffbf173', 'head_branch': 'main', 'conclusion': 'success', 'path': '.github/workflows/gds-strength-residual-screen.yaml'}, 'gate_receipt': {'source_run': 38499287760, 'qualified': True, 'added_buffers': 20, 'resized_cells': 0, 'minimum_fast_hold_ns': 0.05, 'all_original_connections_audited': True, 'source_detailed_wires_cleared': True, 'full_reroute': True, 'custom_image': True, 'physical_screen_only': True, 'official_signoff': False, 'post_antenna_batches': 0, 'post_antenna_buffers': 0, 'maximum_post_antenna_buffers': 64, 'post_antenna_connectivity_audited': True}, 'screen_root': 'runs/strength-residual-screen', 'recipe_path': 'src/config_strength_residual_screen.json', 'baseline_nl': 'runs/strength-fanout-route/drt/1-openroad-detailedrouting/tt_um_tripwire.nl.v', 'baseline_def': 'runs/strength-fanout-route/drt/1-openroad-detailedrouting/tt_um_tripwire.def', 'timing_root': 'runs/extracted-timing/11-openroad-stapostpnr', 'timing_corner_format': '{corner}', 'output_root': 'runs/strength-residual-route', 'saved_extraction_root': 'runs/strength-residual-source-extracted-timing'}
PROFILE.update(plan=plan,validate_change=validate_change,post_antenna_audit=audit)

if __name__=='__main__':route(PROFILE)

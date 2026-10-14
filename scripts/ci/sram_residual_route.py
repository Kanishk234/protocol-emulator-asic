"""Exact qualified SRAM/data residual screen continuation through stock DRT/extraction."""
from combined_physical_route import main as route
from sram_residual_plan import plan,validate_change
from post_antenna_fanout_audit import audit

PROFILE={'source_run': 38637997316, 'run_binding': {'id': 38637997316, 'head_sha': 'f9058ec6b895ec3a401f87988d6c26cfcd9e2a4f', 'head_branch': 'main', 'conclusion': 'success', 'path': '.github/workflows/gds-sram-residual-screen.yaml'}, 'gate_receipt': {'source_run': 38621290574, 'qualified': True, 'added_buffers': 8, 'resized_cells': 0, 'minimum_fast_hold_ns': 0.05, 'all_original_connections_audited': True, 'source_detailed_wires_cleared': True, 'full_reroute': True, 'custom_image': True, 'physical_screen_only': True, 'official_signoff': False, 'post_antenna_batches': 1, 'post_antenna_buffers': 3, 'maximum_post_antenna_buffers': 64, 'post_antenna_connectivity_audited': True}, 'screen_root': 'runs/sram-residual-screen', 'recipe_path': 'src/config_sram_residual_screen.json', 'baseline_nl': 'runs/final-combined-route/drt/1-openroad-detailedrouting/tt_um_tripwire.nl.v', 'baseline_def': 'runs/final-combined-route/drt/1-openroad-detailedrouting/tt_um_tripwire.def', 'timing_root': 'runs/extracted-timing/11-openroad-stapostpnr', 'timing_corner_format': '{corner}', 'output_root': 'runs/sram-residual-route', 'saved_extraction_root': 'runs/sram-residual-source-extracted-timing'}
PROFILE.update(plan=plan,validate_change=validate_change,post_antenna_audit=audit)

if __name__=='__main__':route(PROFILE)

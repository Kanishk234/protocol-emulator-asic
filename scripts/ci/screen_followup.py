"""Fresh global-screen source correction; no detailed route."""
from combined_physical_screen import main as screen
from screen_followup_plan import plan,target_call,validate_change

PROFILE={'source_run': 38347662810, 'run_binding': {'id': 38347662810, 'head_sha': 'cb16ebda06c8b915e2059a10ce606ea1a73c46ae', 'head_branch': 'main', 'conclusion': 'failure', 'path': '.github/workflows/gds-residual-combined-screen.yaml'}, 'source_kind': 'global-screen', 'source_gate_receipt': {'source_run': 38336141213, 'qualified': False, 'added_buffers': 53, 'resized_cells': 3, 'minimum_fast_hold_ns': 0.05, 'all_original_connections_audited': True, 'source_detailed_wires_cleared': True, 'full_reroute': True, 'custom_image': True, 'physical_screen_only': True, 'official_signoff': False}, 'route_root': 'runs/residual-combined-screen', 'output_root': 'runs/screen-followup', 'timing_root': 'runs/residual-combined-screen/timing', 'timing_corner_format': 'after-{corner}/1-openroad-stamidpnr', 'recipe_path': 'src/config_residual_combined_screen.json', 'screen_config': 'src/config_screen_followup.json', 'image': 'tripwire-screen-followup:local', 'dockerfile': 'workflow-src/scripts/ci/Dockerfile.openroad-screen-followup'}
PROFILE.update(plan=plan,target_call=target_call,validate_change=validate_change)

if __name__=='__main__':screen(PROFILE)

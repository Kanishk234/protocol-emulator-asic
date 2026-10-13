"""Fresh timing-clean screen fanout repair; no detailed route."""
from combined_physical_screen import main as screen
from screen_fanout_finish_plan import plan,target_call,validate_change

PROFILE={'source_run': 38349702735, 'run_binding': {'id': 38349702735, 'head_sha': '2dcd16eb188774373a53400a0b1f892cc996e201', 'head_branch': 'main', 'conclusion': 'failure', 'path': '.github/workflows/gds-screen-followup.yaml'}, 'source_kind': 'global-screen', 'source_gate_receipt': {'source_run': 38347662810, 'qualified': False, 'added_buffers': 54, 'resized_cells': 0, 'minimum_fast_hold_ns': 0.05, 'all_original_connections_audited': True, 'source_detailed_wires_cleared': False, 'full_reroute': True, 'custom_image': True, 'physical_screen_only': True, 'official_signoff': False, 'source_global_screen': True, 'source_detailed_wire_reset_count': 0}, 'route_root': 'runs/screen-followup', 'output_root': 'runs/screen-fanout-finish', 'timing_root': 'runs/screen-followup/timing', 'timing_corner_format': 'after-{corner}/1-openroad-stamidpnr', 'recipe_path': 'src/config_screen_followup.json', 'screen_config': 'src/config_screen_fanout_finish.json', 'image': 'tripwire-screen-fanout-finish:local', 'dockerfile': 'workflow-src/scripts/ci/Dockerfile.openroad-screen-followup'}
PROFILE.update(plan=plan,target_call=target_call,validate_change=validate_change)

if __name__=='__main__':screen(PROFILE)

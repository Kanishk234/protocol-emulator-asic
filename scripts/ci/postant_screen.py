"""Source-bound fanout screen with bounded same-process post-antenna repair."""
from combined_physical_screen import main as screen
from postant_screen_plan import plan,target_call,validate_change
from post_antenna_fanout_audit import audit

PROFILE={'source_run': 38353731199, 'run_binding': {'id': 38353731199, 'head_sha': '1b58a13fd9bfa650dccbdea9b6b0add161b9ea29', 'head_branch': 'main', 'conclusion': 'failure', 'path': '.github/workflows/gds-screen-fanout-finish.yaml'}, 'source_kind': 'global-screen', 'source_gate_receipt': {'source_run': 38352108106, 'qualified': False, 'added_buffers': 4, 'resized_cells': 0, 'minimum_fast_hold_ns': 0.05, 'all_original_connections_audited': True, 'source_detailed_wires_cleared': False, 'full_reroute': True, 'custom_image': True, 'physical_screen_only': True, 'official_signoff': False, 'source_global_screen': True, 'source_detailed_wire_reset_count': 0}, 'route_root': 'runs/screen-fanout-finish-v2', 'output_root': 'runs/postant-screen', 'timing_root': 'runs/screen-fanout-finish-v2/timing', 'timing_corner_format': 'after-{corner}/1-openroad-stamidpnr', 'recipe_path': 'src/config_screen_fanout_finish_v2.json', 'screen_config': 'src/config_postant_screen.json', 'image': 'tripwire-postant-screen:local', 'dockerfile': 'workflow-src/scripts/ci/Dockerfile.openroad-postant-fanout'}
PROFILE.update(plan=plan,target_call=target_call,validate_change=validate_change,post_antenna_audit=audit)

if __name__=='__main__':screen(PROFILE)

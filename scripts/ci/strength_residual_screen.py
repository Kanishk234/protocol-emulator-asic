"""Exact timing-passing source residual electrical screen; no resizes."""
from combined_physical_screen import main as screen
from strength_residual_plan import plan,target_call,validate_change
from post_antenna_fanout_audit import audit

PROFILE={'source_run': 38499287760, 'run_binding': {'id': 38499287760, 'head_sha': '0501e0a50a5fb3832c6ac81d6fa48b6fe330555d', 'head_branch': 'main', 'conclusion': 'failure', 'path': '.github/workflows/gds-strength-fanout-route.yaml'}, 'route_root': 'runs/strength-fanout-route', 'output_root': 'runs/strength-residual-screen', 'recipe_path': 'src/config_electrical_incremental_route.json', 'screen_config': 'src/config_strength_residual_screen.json', 'image': 'tripwire-strength-residual:local', 'dockerfile': 'workflow-src/scripts/ci/Dockerfile.openroad-decode-combined'}
PROFILE.update(plan=plan,target_call=target_call,validate_change=validate_change,post_antenna_audit=audit)

if __name__=='__main__':screen(PROFILE)

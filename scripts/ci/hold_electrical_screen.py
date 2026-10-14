"""Exact measured hold and electrical repairs; no resizes."""
from combined_physical_screen import main as screen
from hold_electrical_plan import plan,target_call,validate_change
from post_antenna_fanout_audit import audit

PROFILE={'source_run': 38507730942, 'run_binding': {'id': 38507730942, 'head_sha': 'c242b5a71ae48252fafcafde8d197b202f6001f9', 'head_branch': 'main', 'conclusion': 'failure', 'path': '.github/workflows/gds-strength-residual-route.yaml'}, 'route_root': 'runs/strength-residual-route', 'output_root': 'runs/hold-electrical-screen', 'recipe_path': 'src/config_electrical_incremental_route.json', 'screen_config': 'src/config_hold_electrical_screen.json', 'image': 'tripwire-hold-electrical:local', 'dockerfile': 'workflow-src/scripts/ci/Dockerfile.openroad-decode-combined'}
PROFILE.update(plan=plan,target_call=target_call,validate_change=validate_change,post_antenna_audit=audit)

if __name__=='__main__':screen(PROFILE)

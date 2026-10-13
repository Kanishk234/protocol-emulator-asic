"""Exact latest-source combined strength, data fanout and hold screen."""
from combined_physical_screen import main as screen
from strength_fanout_plan import plan,target_call,validate_change
from post_antenna_fanout_audit import audit

PROFILE={'source_run': 38456657314, 'run_binding': {'id': 38456657314, 'head_sha': 'e6379fb46a48bcc7c3c0942b30b492fe1a25210c', 'head_branch': 'main', 'conclusion': 'failure', 'path': '.github/workflows/gds-fanout-load-route.yaml'}, 'route_root': 'runs/fanout-load-route', 'output_root': 'runs/strength-fanout-screen', 'recipe_path': 'src/config_electrical_incremental_route.json', 'screen_config': 'src/config_strength_fanout_screen.json', 'image': 'tripwire-strength-fanout:local', 'dockerfile': 'workflow-src/scripts/ci/Dockerfile.openroad-strength-fanout'}
PROFILE.update(plan=plan,target_call=target_call,validate_change=validate_change,post_antenna_audit=audit)

if __name__=='__main__':screen(PROFILE)

"""Exact tested NOR2 strength and remaining data fanout physical screen."""
from combined_physical_screen import main as screen
from final_combined_plan import plan,target_call,validate_change
from post_antenna_fanout_audit import audit

PROFILE={'source_run': 38515215944, 'run_binding': {'id': 38515215944, 'head_sha': 'ad0f3ec1fa2bf66341ca79ef00df6f51a09b0066', 'head_branch': 'main', 'conclusion': 'failure', 'path': '.github/workflows/gds-hold-electrical-route.yaml'}, 'route_root': 'runs/hold-electrical-route', 'output_root': 'runs/final-combined-screen', 'recipe_path': 'src/config_electrical_incremental_route.json', 'screen_config': 'src/config_final_combined_screen.json', 'image': 'tripwire-final-combined:local', 'dockerfile': 'workflow-src/scripts/ci/Dockerfile.openroad-final-combined'}
PROFILE.update(plan=plan,target_call=target_call,validate_change=validate_change,post_antenna_audit=audit)

if __name__=='__main__':screen(PROFILE)

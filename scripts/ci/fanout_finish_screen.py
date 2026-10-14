"""Exact final two-data-net fanout repair; strict gates unchanged."""
from combined_physical_screen import main as screen
from fanout_finish_plan import plan,target_call,validate_change
from post_antenna_fanout_audit import audit

PROFILE={'source_run': 38641675550, 'run_binding': {'id': 38641675550, 'head_sha': '44cdfdff239a63813b91f1678dc3503c94f37213', 'head_branch': 'main', 'conclusion': 'failure', 'path': '.github/workflows/gds-sram-residual-route.yaml'}, 'route_root': 'runs/sram-residual-route', 'output_root': 'runs/fanout-finish-screen', 'recipe_path': 'src/config_electrical_incremental_route.json', 'screen_config': 'src/config_fanout_finish_screen.json', 'image': 'tripwire-fanout-finish:local', 'dockerfile': 'workflow-src/scripts/ci/Dockerfile.openroad-decode-combined'}
PROFILE.update(plan=plan,target_call=target_call,validate_change=validate_change,post_antenna_audit=audit)

if __name__=='__main__':screen(PROFILE)

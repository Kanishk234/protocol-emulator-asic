"""Exact data fanout and clock-diode isolation screen; functional clock pins fixed."""
from combined_physical_screen import main as screen
from fanout_load_plan import plan,target_call,validate_change
from post_antenna_fanout_audit import audit

PROFILE={'source_run': 38433037592, 'run_binding': {'id': 38433037592, 'head_sha': '18dd627c8671e82d650b6978236857724cb258fa', 'head_branch': 'main', 'conclusion': 'failure', 'path': '.github/workflows/gds-decode-combined-route.yaml'}, 'route_root': 'runs/decode-combined-route', 'output_root': 'runs/fanout-load-screen', 'recipe_path': 'src/config_electrical_incremental_route.json', 'screen_config': 'src/config_fanout_load_screen.json', 'image': 'tripwire-fanout-load:local', 'dockerfile': 'workflow-src/scripts/ci/Dockerfile.openroad-decode-combined'}
PROFILE.update(plan=plan,target_call=target_call,validate_change=validate_change,post_antenna_audit=audit)

if __name__=='__main__':screen(PROFILE)

"""Exact measured fanout and diode-loaded slew repair; strict gates unchanged."""
from combined_physical_screen import main as screen
from fanout_slew_plan import plan,target_call,validate_change
from post_antenna_fanout_audit import audit

PROFILE={'source_run': 38668749394, 'run_binding': {'id': 38668749394, 'head_sha': 'e54a07b661a53337e16b49aca846cafc0efbef1d', 'head_branch': 'main', 'conclusion': 'failure', 'path': '.github/workflows/gds-fanout-finish-route.yaml'}, 'route_root': 'runs/fanout-finish-route', 'output_root': 'runs/fanout-slew-screen', 'recipe_path': 'src/config_electrical_incremental_route.json', 'screen_config': 'src/config_fanout_slew_screen.json', 'image': 'tripwire-fanout-slew:local', 'dockerfile': 'workflow-src/scripts/ci/Dockerfile.openroad-decode-combined'}
PROFILE.update(plan=plan,target_call=target_call,validate_change=validate_change,post_antenna_audit=audit)

if __name__=='__main__':screen(PROFILE)

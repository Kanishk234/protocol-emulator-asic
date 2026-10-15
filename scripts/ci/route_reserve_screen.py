"""Measured post-route diode/fanout and NAND4 load isolation; screen only."""
from combined_physical_screen import main as screen
from route_reserve_plan import plan,target_call,validate_change
from post_antenna_fanout_audit import audit

PROFILE={'source_run': 38679335674, 'run_binding': {'id': 38679335674, 'head_sha': 'b049a17343b3ff9912f596aa9953be1397c5baf7', 'head_branch': 'main', 'conclusion': 'failure', 'path': '.github/workflows/gds-fanout-slew-route.yaml'}, 'route_root': 'runs/fanout-slew-route', 'output_root': 'runs/route-reserve-screen', 'recipe_path': 'src/config_electrical_incremental_route.json', 'screen_config': 'src/config_route_reserve_screen.json', 'image': 'tripwire-route-reserve:local', 'dockerfile': 'workflow-src/scripts/ci/Dockerfile.openroad-decode-combined'}
PROFILE.update(plan=plan,target_call=target_call,validate_change=validate_change,post_antenna_audit=audit)

def main():
    screen(PROFILE)
    from route_reserve_gate import enforce
    enforce(PROFILE['output_root'])


if __name__ == '__main__':
    main()

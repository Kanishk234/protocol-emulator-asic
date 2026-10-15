"""Bounded 64-net preventive electrical repair with calibrated screen margins."""
from combined_physical_screen import main as screen
from margin_risk_plan import plan,target_call,validate_change
from post_antenna_fanout_audit import audit

PROFILE={'source_run': 38689478738, 'run_binding': {'id': 38689478738, 'head_sha': '54c32ceb682e3cbd7deb68e83c5d4b6400e0ad5f', 'head_branch': 'main', 'conclusion': 'failure', 'path': '.github/workflows/gds-route-reserve-route.yaml'}, 'route_root': 'runs/route-reserve-route', 'output_root': 'runs/margin-risk-screen', 'recipe_path': 'src/config_electrical_incremental_route.json', 'screen_config': 'src/config_margin_risk_screen.json', 'image': 'tripwire-margin-risk:local', 'dockerfile': 'workflow-src/scripts/ci/Dockerfile.openroad-decode-combined'}
PROFILE['electrical_margin_tcl']='workflow-src/scripts/ci/electrical_margin_probe.tcl'
PROFILE.update(plan=plan,target_call=target_call,validate_change=validate_change,post_antenna_audit=audit)

def main():
    screen(PROFILE)
    from route_reserve_gate import enforce
    enforce(PROFILE['output_root'])
    from electrical_margin_gate import enforce as margin_gate
    margin_gate(PROFILE['output_root'])


if __name__ == '__main__':
    main()

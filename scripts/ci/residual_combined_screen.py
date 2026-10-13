"""Improved-source residual setup/hold/electrical screen; never DRT."""
from combined_physical_screen import main as screen
from residual_combined_plan import plan,target_call,validate_change

PROFILE=dict(source_run=38336141213,
    run_binding=dict(id=38336141213,head_sha='a1642e654ceaae36ee082555e1144b728e3fcb22',head_branch='main',conclusion='failure',path='.github/workflows/gds-combined-physical-route.yaml'),
    route_root='runs/combined-physical-route',output_root='runs/residual-combined-screen',
    recipe_path='src/config_electrical_incremental_route.json',screen_config='src/config_residual_combined_screen.json',
    image='tripwire-residual-combined:local',dockerfile='workflow-src/scripts/ci/Dockerfile.openroad-residual-combined',
    plan=plan,target_call=target_call,validate_change=validate_change)


if __name__=='__main__':screen(PROFILE)

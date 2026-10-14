"""Exact timing-passing source SRAM and data-load residual screen."""
from combined_physical_screen import main as screen
from sram_residual_plan import plan,target_call,validate_change
from post_antenna_fanout_audit import audit

PROFILE={'source_run': 38621290574, 'run_binding': {'id': 38621290574, 'head_sha': '372fcace90fd6bc278a099dcc7fd677dc7134bae', 'head_branch': 'main', 'conclusion': 'failure', 'path': '.github/workflows/gds-final-combined-route.yaml'}, 'route_root': 'runs/final-combined-route', 'output_root': 'runs/sram-residual-screen', 'recipe_path': 'src/config_electrical_incremental_route.json', 'screen_config': 'src/config_sram_residual_screen.json', 'image': 'tripwire-sram-residual:local', 'dockerfile': 'workflow-src/scripts/ci/Dockerfile.openroad-decode-combined'}
PROFILE.update(plan=plan,target_call=target_call,validate_change=validate_change,post_antenna_audit=audit)

if __name__=='__main__':screen(PROFILE)

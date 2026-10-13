"""Extracted-source combined decode/hold/electrical screen; no DRT."""
from combined_physical_screen import main as screen
from decode_combined_plan import plan,target_call,validate_change
from post_antenna_fanout_audit import audit

PROFILE={'source_run': 38358706808, 'run_binding': {'id': 38358706808, 'head_sha': '8e77722239af612fad2f590c322cab84600f76d0', 'head_branch': 'main', 'conclusion': 'failure', 'path': '.github/workflows/gds-postant-route.yaml'}, 'route_root': 'runs/postant-route', 'output_root': 'runs/decode-combined-screen', 'recipe_path': 'src/config_electrical_incremental_route.json', 'screen_config': 'src/config_decode_combined_screen.json', 'image': 'tripwire-decode-combined:local', 'dockerfile': 'workflow-src/scripts/ci/Dockerfile.openroad-decode-combined'}
PROFILE.update(plan=plan,target_call=target_call,validate_change=validate_change,post_antenna_audit=audit)

if __name__=='__main__':screen(PROFILE)

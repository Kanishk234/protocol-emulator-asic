"""Reaudit and freshly qualify the completed inline GRT; no physical edits repeated."""
from combined_physical_screen import main as screen
from inline_margin_screen import PROFILE as BASE
from route_reserve_gate import enforce as fanout_gate
from electrical_margin_gate import enforce as margin_gate

PROFILE=dict(BASE,resume_grt_run=dict(id=38773856018,
    head_sha='0e37feb50922926a4eaaedf7826614c94d4a67d5',head_branch='main',
    conclusion='failure',path='.github/workflows/gds-inline-margin-screen.yaml'))

if __name__=='__main__':
    screen(PROFILE)
    fanout_gate(PROFILE['output_root'])
    margin_gate(PROFILE['output_root'])

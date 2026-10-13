"""Exact fresh-screen hold/fanout repair; retain all previous repairs."""
from combined_physical_plan import plan as build,target_call as emit,validate_change as conserve

BINDING={'source_run': 38347662810, 'nl_sha': '851bfcb3442975838dfd9ae34eddc30e915d1e63a09a434d1b1997560f960946', 'def_sha': '07e31c7814b93945e7b9b332c1068f3f7d330dbb89c1ff322ff3434ba00164be', 'report_sha': '3e351ca1369b2902d55d2b18b22c7b1f5d3b2750fad746a0205e4c7b4c5fbfc1', 'checks_sha': {'nom_fast_1p32V_m40C': '60ddc1f943c3a1248c2d3ca1d7807bf9e7102a2920085c72f5f97205d61eeea7', 'nom_typ_1p20V_25C': '2965f7a8b08ac494dab19e2dafb674b951a2fae6fac0fa4ec60e24b7ac9c6a71', 'nom_slow_1p08V_125C': 'dbc2edea052bf16d4d40e0357c7b82122c7556c5f1550c124bfc422d4bc6d952'}, 'prefix': 'tripwire_screen_followup_', 'hold_count': 47, 'hold_target_ns': 0.075, 'electrical_nets': 2, 'setup': {}, 'targets': {}}


def plan(*args):return build(*args,binding=BINDING)

def target_call(layout,proposal):return emit(layout,proposal,binding=BINDING)

def validate_change(before,after,proposal):return conserve(before,after,proposal,binding=BINDING)

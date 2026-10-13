"""Exact fresh-screen fanout-only repair; retain all previous repairs."""
from combined_physical_plan import plan as build,target_call as emit,validate_change as conserve

BINDING={'source_run': 38353731199, 'nl_sha': '10e11b269b86642b3528f7d87ca6e9aeaa5c742de1feceb6a501e9822c675c25', 'def_sha': '77d23915271e5a361d7e7832511e865a3c2d88b07194fa94230b44c22e6f0e86', 'report_sha': '72461bcc0cbbe56cf697bb6fe93a1fcd43faf2ee7a248e1659e7240935696ba0', 'checks_sha': {'nom_fast_1p32V_m40C': 'dcb22fa15c3e64b322d2f5124b2fe895c99f27fe6b9beb084b9f08117c71d0af', 'nom_typ_1p20V_25C': '6c5490beade2e6dd17837b509863a895f7fbbe8490bf13366d0b9626a7b5d9b7', 'nom_slow_1p08V_125C': '85a6ffb131f92ce009f66772b2a330adf41cb267c3844534d3a1e442b2b938e7'}, 'prefix': 'tripwire_postant_screen_', 'hold_count': 0, 'hold_target_ns': 0.05, 'electrical_nets': 2, 'setup': {}, 'targets': {}}


def plan(*args):return build(*args,binding=BINDING)

def target_call(layout,proposal):return emit(layout,proposal,binding=BINDING)

def validate_change(before,after,proposal):return conserve(before,after,proposal,binding=BINDING)

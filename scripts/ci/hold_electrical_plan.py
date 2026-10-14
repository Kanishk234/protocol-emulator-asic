"""Exact extracted hold-reserve and four-net electrical repair."""
from combined_physical_plan import plan as build,target_call as emit,validate_change as conserve

BINDING={'source_run': 38507730942, 'nl_sha': '186a1b5b2119c61a7b5d148e6eff254c3dac853210be92e3c43a7b287c50f9c2', 'def_sha': 'ccb3ed07ba2ff4356ca46b4915252780e0af532c0c20e896f6ffd12a951b2397', 'report_sha': 'de152b951438ba60923a2d40d8768a3ce77ef7d45ababb99e237732e5666783d', 'checks_sha': {'nom_fast_1p32V_m40C': '5125cb9816d900939405453e00f7ac10a42e2fc67c2cb9e3ff3e9df553e0be1c', 'nom_typ_1p20V_25C': '2d84f0edc2d80bd45b4b3519bd84793899519a1f8742c0054bccc06b8ed96b92', 'nom_slow_1p08V_125C': '0d1259d6ce04bd1f780844557d73665be46a33c62df4017efa9ab5f32e573e89'}, 'prefix': 'tripwire_hold_electrical_', 'hold_count': 132, 'hold_target_ns': 0.1, 'electrical_nets': 4, 'setup': {}, 'targets': {}, 'normalize_instances': True}


def plan(*args):return build(*args,binding=BINDING)

def target_call(layout,proposal):return emit(layout,proposal,binding=BINDING)

def validate_change(before,after,proposal):return conserve(before,after,proposal,binding=BINDING)

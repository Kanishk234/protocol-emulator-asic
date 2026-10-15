"""Measured seven-net load isolation; source-bound with reserved fanout slots."""
from combined_physical_plan import plan as build, target_call as emit, validate_change as conserve

BINDING={'source_run': 38679335674, 'nl_sha': '45ca4297c02122d9bb7db9cbb2935b051751b6386a750a6c32cf91a2003a4299', 'def_sha': '37a474ae4f5e574729012f2f987479b0415dee3f3e0ae9e4cf1ce3902a94cb95', 'report_sha': '9d3bc2bc01c8cdfd8b8109dc302c5bc3c342de01ab1b0c2b8282d80009a608d2', 'checks_sha': {'nom_typ_1p20V_25C': '435f849bd9e9b5b2be6d1f6de785bc275c8d87d1e63e4a8765d7ac01c12ce573', 'nom_slow_1p08V_125C': '2c6167ebd9404f3ebd98ecb88d467948df885dc53fefbdee4b4db35c652abdaa', 'nom_fast_1p32V_m40C': 'cded067a7a9f5c004524a67fabb19fc0d86bb7977927258f35d943d3e4a2fa87'}, 'prefix': 'tripwire_route_reserve_38679335674_', 'hold_count': 0, 'hold_target_ns': 0.075, 'electrical_nets': 7, 'setup': {}, 'targets': {}, 'normalize_instances': True}


def plan(*args):
    proposal = build(*args, binding=BINDING)
    if proposal["added_buffers"] != 19:
        raise ValueError("Wrong reviewed reserve buffer count")
    return proposal


def target_call(layout, proposal):
    return emit(layout, proposal, binding=BINDING)


def validate_change(before, after, proposal):
    return conserve(before, after, proposal, binding=BINDING)

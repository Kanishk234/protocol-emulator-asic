"""Exact three-source fanout and slew load isolation; retain timing repairs."""
from combined_physical_plan import plan as build,target_call as emit,validate_change as conserve

BINDING={'source_run': 38668749394, 'nl_sha': 'd71a9f1c2ab57651ac5adfc9797716dd48eece9f5a073ece8b5517f6bff0ebc2', 'def_sha': 'fc4d15e83c339848a3c4b6d1097131309fd325ed0abb5ab890921de33837d58a', 'report_sha': '6e1d45e5ad3fa0cbb7430454975bbcca840dff200c369e041e0d50ca10bcfafd', 'checks_sha': {'nom_fast_1p32V_m40C': '6bd086d99fb4bfa5c460e09010ba2f646873d4c3fc50a785673c53cdf2cfdbf6', 'nom_typ_1p20V_25C': '277c001ab7f0ee5e45183c81b7694b63529ab308b49e5df3e67620a036ff68d0', 'nom_slow_1p08V_125C': '0628447f9355f1f3aae0294587b3832559f988c754df8082093661fb03fb2dfa'}, 'prefix': 'tripwire_fanout_slew_38668749394_', 'hold_count': 0, 'hold_target_ns': 0.075, 'electrical_nets': 3, 'setup': {}, 'targets': {}, 'normalize_instances': True}


def plan(*args):return build(*args,binding=BINDING)

def target_call(layout,proposal):return emit(layout,proposal,binding=BINDING)

def validate_change(before,after,proposal):return conserve(before,after,proposal,binding=BINDING)

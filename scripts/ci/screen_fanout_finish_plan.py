"""Exact fresh-screen fanout-only repair; retain all previous repairs."""
from combined_physical_plan import plan as build,target_call as emit,validate_change as conserve

BINDING={'source_run': 38349702735, 'nl_sha': 'ee5597b7dabd821453f42f62746a12f23e7d9ca95ed3d24c48651db95ecb4921', 'def_sha': 'bd3c676fcb27f8d0f6b09543c8512f73a9b9171d57474b645646f348879bbb38', 'report_sha': '59be915f27bc0c72a4b1869b6ac031938312171a2084b7731106331f214d15d6', 'checks_sha': {'nom_fast_1p32V_m40C': 'a51a6725a30ba6531b7fd562d07ae446e1bf65112e87ff7d4bccb64a93a9ff10', 'nom_typ_1p20V_25C': '770bc0acfa6e1f488c1445180940cffa6440e5bface583f4e564c79f3dcacad9', 'nom_slow_1p08V_125C': 'e571e89767b24afd58de605886f88880cac5ec6d668cb31aeec9177255b48d6b'}, 'prefix': 'tripwire_fanout_finish_', 'hold_count': 0, 'hold_target_ns': 0.075, 'electrical_nets': 2, 'setup': {}, 'targets': {}}


def plan(*args):return build(*args,binding=BINDING)

def target_call(layout,proposal):return emit(layout,proposal,binding=BINDING)

def validate_change(before,after,proposal):return conserve(before,after,proposal,binding=BINDING)

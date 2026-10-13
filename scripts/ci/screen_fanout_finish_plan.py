"""Exact fresh-screen fanout-only repair; retain all previous repairs."""
from combined_physical_plan import plan as build,target_call as emit,validate_change as conserve

BINDING={'source_run': 38352108106, 'nl_sha': '3751a3e59a3eb03f4e47375467427fe43cabee7fbc6979ddb8a748b111c3ddcb', 'def_sha': 'aeb3147060e978849dc225b4baeb2123301b9c943c3ff4d67447b502fc46be2d', 'report_sha': '8aa036d1475f906fd98c85cdbb0332bda755bc96589cfb61270f32257697cf36', 'checks_sha': {'nom_fast_1p32V_m40C': 'c82c5d8c6312307dd0c4cc8d18b80b9712954b2ab7e93856dae7737ff158a019', 'nom_typ_1p20V_25C': 'da0c61f27562c035871a53cdffdcbcf52104d67014b5f63fa004bfbcbc43c3ea', 'nom_slow_1p08V_125C': 'c5c88f9acd9d2c36302c4652d245190d4b4bb8dedc40dac12018f0b7a063c81d'}, 'prefix': 'tripwire_fanout_finish_v2_', 'hold_count': 0, 'hold_target_ns': 0.075, 'electrical_nets': 1, 'setup': {}, 'targets': {}}


def plan(*args):return build(*args,binding=BINDING)

def target_call(layout,proposal):return emit(layout,proposal,binding=BINDING)

def validate_change(before,after,proposal):return conserve(before,after,proposal,binding=BINDING)

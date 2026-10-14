"""Exact extracted residual data-load repair; preserve all timing gains."""
from combined_physical_plan import plan as build,target_call as emit,validate_change as conserve

BINDING={'source_run': 38499287760, 'nl_sha': 'b5077175782fc2738c2dc03c8e3fac00b2753e84c8e0f9a128eff0e9d7148f18', 'def_sha': 'e1bdba97d3ef126affb301ea354800a0d071a533ad134259618f34e027f955b1', 'report_sha': '4af0d1eab5d949ed161d7da536dbd32bb8fcdd57b51843d82870c0db3a8dba10', 'checks_sha': {'nom_fast_1p32V_m40C': '4f6e9eec64f933ecba934e48eb8734bb4238092fa29ae525bfee183e6e043bd3', 'nom_typ_1p20V_25C': '91370f00e0a9468523f90557337d683a4132c363030d096f17c8401c8b97462f', 'nom_slow_1p08V_125C': '5b1e18b2255df6101dc7d6c2210b54f928cb45b6191521336c6be9657f2a5102'}, 'prefix': 'tripwire_strength_residual_', 'hold_count': 0, 'hold_target_ns': 0.075, 'electrical_nets': 7, 'setup': {}, 'targets': {}, 'normalize_instances': True}


def plan(*args):return build(*args,binding=BINDING)

def target_call(layout,proposal):return emit(layout,proposal,binding=BINDING)

def validate_change(before,after,proposal):return conserve(before,after,proposal,binding=BINDING)

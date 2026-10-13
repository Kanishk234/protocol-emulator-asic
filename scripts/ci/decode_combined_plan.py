"""Exact fresh-screen fanout-only repair; retain all previous repairs."""
from combined_physical_plan import plan as build,target_call as emit,validate_change as conserve

BINDING={'source_run': 38358706808, 'nl_sha': 'ef42b80d7bf616ba228530506ae78368d88a15d36793a3b4efbb89de5fa77525', 'def_sha': '9a5383502a7b0d062e2ab5ae24ba517b984434ddd66a5bcf467e1eed8de0db96', 'report_sha': 'b578bb91fdea54c1a62928998ee794f41e49e8bc90dc9d21b1ae1cf5d9bb7d94', 'checks_sha': {'nom_fast_1p32V_m40C': '0aa8a283f55302ac4a70bc3e37b490be957fb38b641112ea5c7eccde1683e04f', 'nom_typ_1p20V_25C': '2389a74c06dd988475f93ef3df2bc84eeb7b6b5d0f2473dc19ff0bf6b506ccf2', 'nom_slow_1p08V_125C': '3137d7eb1852c5d140dae29a045ca7f790a2bf62e194b0b0aba0875acfcd8844'}, 'prefix': 'tripwire_decode_combined_', 'hold_count': 4, 'hold_target_ns': 0.075, 'electrical_nets': 12, 'setup': {'_30044_': 'sg13cmos5l_a21oi_2', '_43917_': 'sg13cmos5l_nor2_2'}, 'targets': {'_30044_': ('sg13cmos5l_a21oi_1', 'sg13cmos5l_a21oi_2'), '_43917_': ('sg13cmos5l_nor2_1', 'sg13cmos5l_nor2_2')}}


def plan(*args):return build(*args,binding=BINDING)

def target_call(layout,proposal):return emit(layout,proposal,binding=BINDING)

def validate_change(before,after,proposal):return conserve(before,after,proposal,binding=BINDING)

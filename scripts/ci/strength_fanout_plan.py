"""Exact tested setup/slew strengths and remaining data fanout repair."""
from combined_physical_plan import plan as build,target_call as emit,validate_change as conserve

BINDING={'source_run': 38456657314, 'nl_sha': '0e1a8a9101636d103a0a78a953c8c1452cf22118e626167381d7d791cd9d6d15', 'def_sha': 'a7500ea3c4e36ced68f032cf7587ab4ed982060693213ed15e568c0e3862b96e', 'report_sha': 'f5c106ca53a3348ef09c2893e79c78871be27a0aef6ec30213d28cbcc0071144', 'checks_sha': {'nom_fast_1p32V_m40C': 'ba6ddde66b361bd4370391b086992892ffc5a96fac294232c4341984b67b2460', 'nom_typ_1p20V_25C': '141bbf7575b53541697e597354c65dab13bfdf3e05584dba694ae6785aa0a9ba', 'nom_slow_1p08V_125C': '50471224e17819fcadd62091cb91f0beff8c3b9254cc8a07fbf83f9a1931a5f9'}, 'prefix': 'tripwire_strength_fanout_', 'hold_count': 9, 'hold_target_ns': 0.075, 'electrical_nets': 6, 'setup': {'_27477_': 'sg13cmos5l_nand2_2', '_27475_': 'sg13cmos5l_a21oi_2', '_29456_': 'sg13cmos5l_nor2_2', '_29529_': 'sg13cmos5l_nand2_2'}, 'targets': {'_27477_': ('sg13cmos5l_nand2_1', 'sg13cmos5l_nand2_2'), '_27475_': ('sg13cmos5l_a21oi_1', 'sg13cmos5l_a21oi_2'), '_29456_': ('sg13cmos5l_nor2_1', 'sg13cmos5l_nor2_2'), '_29529_': ('sg13cmos5l_nand2_1', 'sg13cmos5l_nand2_2')}, 'normalize_instances': True, 'resize_only_slew_drivers': ['_29456_', '_29529_']}


def plan(*args):return build(*args,binding=BINDING)

def target_call(layout,proposal):return emit(layout,proposal,binding=BINDING)

def validate_change(before,after,proposal):return conserve(before,after,proposal,binding=BINDING)

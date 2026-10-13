"""Exact improved-source residual physical proposal, not qualification."""
from combined_physical_plan import plan as build, target_call as emit, validate_change as conserve

BINDING={'source_run': 38336141213, 'nl_sha': 'c98fb068c21b40c07263a67f63e446e1099f8116b5a9fb0806841ea612e7d386', 'def_sha': 'c28307f932c670729b1abb6fe5f987c49f659adb1897fc57dbf73b504b2524f7', 'report_sha': '49edb78c44a42175c5fc5372baa25b901f240c53099b4cf463e592b7255822d8', 'checks_sha': {'nom_typ_1p20V_25C': '27b06693f528cad36df91ec9596318fc875bbc62bbe94faab9134510cc961a39', 'nom_slow_1p08V_125C': '24f29f82a77eb295af61016d2c2b99a69507acc6940772b142e14e31b098c4c9', 'nom_fast_1p32V_m40C': '2b280d6614012a097e6df71ccbedc594ac7c4166ab6c6b52c7b24d6c85159c3e'}, 'prefix': 'tripwire_residual_', 'hold_count': 32, 'hold_target_ns': 0.075, 'electrical_nets': 8, 'targets': {'_43582_': ('sg13cmos5l_nor2_1', 'sg13cmos5l_nor2_2'), 'hold12766': ('sg13cmos5l_dlygate4sd3_1', 'sg13cmos5l_dlygate4sd2_1'), '_43311_': ('sg13cmos5l_nor4_1', 'sg13cmos5l_nor4_2')}, 'setup': {'_43582_': 'sg13cmos5l_nor2_2', 'hold12766': 'sg13cmos5l_dlygate4sd2_1', '_43311_': 'sg13cmos5l_nor4_2'}}


def plan(*args):
    return build(*args,binding=BINDING)


def target_call(layout,proposal):
    return emit(layout,proposal,binding=BINDING)


def validate_change(before,after,proposal):
    return conserve(before,after,proposal,binding=BINDING)

"""Exact tested one-gate setup correction plus three data-fanout repairs."""
from combined_physical_plan import plan as build,target_call as emit,validate_change as conserve

BINDING={'source_run': 38515215944, 'nl_sha': '338223331d30083905f7d105af198e98ba68440af8ba76fb8006f2e899804f0a', 'def_sha': 'a97a0e742ac6d426e6a50a31e840b67bab9ba1a05c8a30da954766e1d928547b', 'report_sha': '8b09d7c58470061bda156b59c1ab6996d197cb27d5c5d9fa30d94b5a3f4031b8', 'checks_sha': {'nom_fast_1p32V_m40C': '1c9f9ebea80d6aa32380e8062500bce99ddb895abc0e759d9b902a3e694c8e11', 'nom_typ_1p20V_25C': 'edb3aebb80890e2ceb31d149dd08ae9751df530c8e6ddffe92102a9885b8a8ff', 'nom_slow_1p08V_125C': '993a7654267df8977c5ce1aeaf6a6e7965fafd6e3dc055b4f5f8eea2a5c8332e'}, 'prefix': 'tripwire_final_combined_', 'hold_count': 0, 'hold_target_ns': 0.075, 'electrical_nets': 3, 'setup': {'_24896_': 'sg13cmos5l_nor2_2'}, 'targets': {'_24896_': ('sg13cmos5l_nor2_1', 'sg13cmos5l_nor2_2')}, 'normalize_instances': True}


def plan(*args):return build(*args,binding=BINDING)

def target_call(layout,proposal):return emit(layout,proposal,binding=BINDING)

def validate_change(before,after,proposal):return conserve(before,after,proposal,binding=BINDING)

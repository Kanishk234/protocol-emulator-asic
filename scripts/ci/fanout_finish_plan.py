"""Exact two-net data fanout repair on timing-passing SRAM route."""
from combined_physical_plan import plan as build,target_call as emit,validate_change as conserve

BINDING={'source_run': 38641675550, 'nl_sha': 'b449cc8d814bf58e83de38ed354593110c2ea6507e4563d4308ea4ef3084a1ef', 'def_sha': '24549ef56894ca71064f22e752662ce1b215e24904633a3fa51b32c7a3fe3791', 'report_sha': 'c5c01a3f73219f3ed156ad5b62a4297fb6d1bb5dd9ce9f6529eb342e9d837463', 'checks_sha': {'nom_fast_1p32V_m40C': '7f2f967b98b5b898dc2d47b5051195c3457daeb61c07912e95122d649876c858', 'nom_typ_1p20V_25C': 'e1d5f3bf1d5e23f7e64715a3f54d52a4c927a523844311405310a355f6bb7360', 'nom_slow_1p08V_125C': 'f80e8d82c47593a719d37a9029d7716dde4915cf0cc8558708dcf8e674bd421c'}, 'prefix': 'tripwire_fanout_finish_38641675550_', 'hold_count': 0, 'hold_target_ns': 0.075, 'electrical_nets': 2, 'setup': {}, 'targets': {}, 'normalize_instances': True}


def plan(*args):return build(*args,binding=BINDING)

def target_call(layout,proposal):return emit(layout,proposal,binding=BINDING)

def validate_change(before,after,proposal):return conserve(before,after,proposal,binding=BINDING)

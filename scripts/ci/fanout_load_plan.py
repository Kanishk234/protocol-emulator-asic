"""Exact fresh-screen fanout-only repair; retain all previous repairs."""
from combined_physical_plan import plan as build,target_call as emit,validate_change as conserve

BINDING={'source_run': 38433037592, 'nl_sha': 'e10b4e2a72e078340da18bd96fb7aa32cbbf02eac782d06a31684016f0d5c0f4', 'def_sha': '707d69eeefbc4dbff178e6ee8747ae4ec154b352063f14392bdd16cf8da97d61', 'report_sha': 'e0757a39e3fc677b16d40417e7095ca8680def4a6ccb461cd7e83cc38a08ae58', 'checks_sha': {'nom_fast_1p32V_m40C': 'd064642a8cb34a9258122f6df3c545025f6ee64ae288150f53e8b2a264213be2', 'nom_typ_1p20V_25C': '312d76cb181117872540fa8b37775c348f6a13f3dafe1f835f22c819c73bad6f', 'nom_slow_1p08V_125C': 'c9da5f3bb74116564906d099fab956c89368af20fa51b8fae556feb35285fd75'}, 'prefix': 'tripwire_fanout_load_', 'hold_count': 2, 'hold_target_ns': 0.075, 'electrical_nets': 9, 'setup': {}, 'targets': {}, 'normalize_instances': True, 'clock_diode_sources': ['clknet_1_0__leaf_u_chip.g_unit[0].u_cfg.g_word[3].g_stored.gclk'], 'clock_driver': 'clkbuf_1_0__f_u_chip.g_unit[0].u_cfg.g_word[3].g_stored.gclk'}


def plan(*args):return build(*args,binding=BINDING)

def target_call(layout,proposal):return emit(layout,proposal,binding=BINDING)

def validate_change(before,after,proposal):return conserve(before,after,proposal,binding=BINDING)

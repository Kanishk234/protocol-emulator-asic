"""Exact SRAM address/output and two data-fanout load repairs."""
from combined_physical_plan import plan as build,target_call as emit,validate_change as conserve

BINDING={'source_run': 38621290574, 'nl_sha': '4727124966b04edf5657c61c4dea5fc14d395323dc503e5d3c237b18b6619ce8', 'def_sha': '9cb63339d99eb09426c93bc84181e0ae78e56d9af07f520abc0b1389b7c31956', 'report_sha': '5436738ab14cdeec21dc6e340db668bdf0f48f4e57b07e338d45789b94c23d16', 'checks_sha': {'nom_fast_1p32V_m40C': 'b8eea0db49f416ee4d70907af3b8d7b4d5474c84811bd35df46a90853b503aa0', 'nom_typ_1p20V_25C': '482aba12c5815720caf6a840fe2a0e7752e932f5c059751262ad5005432f3113', 'nom_slow_1p08V_125C': '263af1774fb1e5fe450d3d11a85280376b77acc7f4b000c30571d02eb4c75f44'}, 'prefix': 'tripwire_sram_residual_', 'hold_count': 0, 'hold_target_ns': 0.075, 'electrical_nets': 4, 'setup': {}, 'targets': {}, 'normalize_instances': True}


def plan(*args):return build(*args,binding=BINDING)

def target_call(layout,proposal):return emit(layout,proposal,binding=BINDING)

def validate_change(before,after,proposal):return conserve(before,after,proposal,binding=BINDING)

"""Functional-only protocol replay of the exact clean preparation netlist."""
from pathlib import Path
from wire600_clean_route import review, validate_bundle
from wire600_selective_plan import digest


def validate(root, run):
    validate_bundle(root, run)
    bound = review()
    netlist = Path(root)/bound['netlist']
    if digest(netlist) != bound['files'][bound['netlist']]:
        raise ValueError('Wrong clean preparation netlist')
    text = netlist.read_text()
    if 'module tt_um_tripwire' not in text or 'RM_IHPSG13_1P_512x16_c2_bm_bist' not in text:
        raise ValueError('Full clean chip SRAM netlist missing')
    return dict(netlist=str(netlist), sha256=digest(netlist), source_run=run['id'],
                functional_simulation_only=True, official_signoff=False,
                detailed_routing_proven=False)

"""Functional-only protocol replay of the exact clean preparation netlist."""
from pathlib import Path
from wire600_clean_route import ROOT, review, validate_bundle
from wire600_selective_plan import digest


def validate(root, run, *, bound=None, screen_root=ROOT):
    bound = review() if bound is None else bound
    validate_bundle(root, run, bound=bound, screen_root=screen_root)
    netlist = Path(root)/bound['netlist']
    if digest(netlist) != bound['files'][bound['netlist']]:
        raise ValueError('Wrong clean preparation netlist')
    text = netlist.read_text()
    if 'module tt_um_tripwire' not in text or 'RM_IHPSG13_1P_512x16_c2_bm_bist' not in text:
        raise ValueError('Full clean chip SRAM netlist missing')
    return dict(netlist=str(netlist), sha256=digest(netlist), source_run=run['id'],
                functional_simulation_only=True, official_signoff=False,
                detailed_routing_proven=False)

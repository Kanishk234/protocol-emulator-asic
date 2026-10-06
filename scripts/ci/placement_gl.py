"""Validate the placement-route artifact before functional gate simulation."""
import hashlib
import json
from pathlib import Path
from route_source import validate_saved


def validate(root):
    validate_saved(root)
    route = root / 'runs/placement-route'
    gates = json.loads((route / 'gates.json').read_text())
    if gates['timing_and_antenna_pass'] is not True:
        raise ValueError('Source timing/antenna gate failed')
    states = list((route / 'drt').glob('*-openroad-detailedrouting/state_out.json'))
    if len(states) != 1:
        raise ValueError('Exactly one completed route required')
    step = states[0].parent
    state = json.loads(states[0].read_text())
    if state['metrics']['route__drc_errors'] != 0:
        raise ValueError('Dirty route')
    netlist = step / 'tt_um_tripwire.nl.v'
    expected = '/runs/placement-route/drt/' + step.name + '/tt_um_tripwire.nl.v'
    if not state['nl'].endswith(expected):
        raise ValueError('Wrong saved netlist')
    config = json.loads((step / 'config.json').read_text())
    if float(config['CLOCK_PERIOD']) != 20 or float(config['GRT_ADJUSTMENT']) != 0.16:
        raise ValueError('Wrong clock/routing settings')
    if not config['PNR_SDC_FILE'].endswith('/src/signoff.sdc'):
        raise ValueError('Wrong constraints')
    source = json.loads((root / 'src/config_rx_screen.json').read_text())
    if source['PL_TIMING_DRIVEN'] is not True or source['PL_OPTIMIZE_MIRRORING'] is not False:
        raise ValueError('Wrong placement policy')
    text = netlist.read_text()
    if 'module tt_um_tripwire' not in text or 'RM_IHPSG13_1P_512x16_c2_bm_bist' not in text:
        raise ValueError('Wrong chip/SRAM netlist')
    return hashlib.sha256(netlist.read_bytes()).hexdigest()

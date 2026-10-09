"""Select a provenance-checked native routed netlist for functional GL."""
import hashlib
import json
from pathlib import Path

SOURCES = {
    37859526262: ('c2d7c8b1094edd4551cc6078ece502a2758c7255', 'stock125',
                  37853023857, 'gds-native-stock-route'),
    37870374707: ('73a35ce3d22d0b63f213078cdeddc5565f0c1d97', 'hold100',
                  37866086829, 'gds-native-hold100-route'),
}


def validate(root, run):
    """GL is functional evidence, including for a timing-failing routed design."""
    expected = SOURCES.get(run['id'])
    if expected is None:
        raise ValueError('Unreviewed native routing run')
    sha, profile, source, workflow = expected
    if (run.get('head_sha') != sha or run.get('head_branch') != 'main'
            or run.get('conclusion') != 'success'
            or run.get('path') != f'.github/workflows/{workflow}.yaml'):
        raise ValueError('Native routing provenance mismatch')
    route = root / 'runs/native-stock-route'
    gates = json.loads((route / 'gates.json').read_text())
    if (gates.get('qualified') is not True or gates.get('profile') != profile
            or gates.get('source_run') != source
            or gates.get('minimum_fast_hold_ns') != 0.05):
        raise ValueError('Native pre-route qualification mismatch')
    states = list((route / 'drt').glob('*-openroad-detailedrouting/state_out.json'))
    if len(states) != 1:
        raise ValueError('Exactly one completed DRT checkpoint required')
    state = json.loads(states[0].read_text())
    if state.get('metrics', {}).get('route__drc_errors') != 0:
        raise ValueError('Native route DRC failure')
    step = states[0].parent
    netlist = step / 'tt_um_tripwire.nl.v'
    suffix = '/runs/native-stock-route/drt/' + step.name + '/tt_um_tripwire.nl.v'
    if not str(state.get('nl', '')).endswith(suffix):
        raise ValueError('Native route netlist identity mismatch')
    config = json.loads((step / 'config.json').read_text())
    if (config.get('CLOCK_PERIOD') != 20
            or config.get('GRT_ADJUSTMENT') != 0.16
            or not str(config.get('PNR_SDC_FILE', '')).endswith('/src/signoff.sdc')):
        raise ValueError('Native route configuration mismatch')
    recipe = json.loads((root / 'src/config_native_stock.json').read_text())
    if (recipe.get('CLOCK_PERIOD') != 20 or recipe.get('SYNTH_STRATEGY') != 'AREA 1'
            or recipe.get('GRT_ADJUSTMENT') != 0.16
            or recipe.get('GRT_RESIZER_HOLD_SLACK_MARGIN') != (0.10 if profile == 'hold100' else 0.125)
            or not str(recipe.get('PNR_SDC_FILE', '')).endswith('/src/signoff.sdc')):
        raise ValueError('Native full recipe mismatch')
    text = netlist.read_text()
    if ('module tt_um_tripwire' not in text
            or 'RM_IHPSG13_1P_512x16_c2_bm_bist' not in text):
        raise ValueError('Full-chip SRAM netlist missing')
    return {'netlist': str(netlist), 'sha256': hashlib.sha256(netlist.read_bytes()).hexdigest(),
            'route_run': run['id'], 'profile': profile,
            'functional_simulation_only': True, 'official_signoff': False}

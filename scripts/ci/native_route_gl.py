"""Select a provenance-checked native routed netlist for functional GL."""
import hashlib
import json
from pathlib import Path
import re

STRENGTH_NETLIST_SHA = 'd5cc09ed3a7db5cbf941fbcacc30347ffac0f3a8488f56b964b9d46f36e327dc'

SOURCES = {
    37954320974: ('dffa228c710ff69749c70bb64ab38df056ed0f21', 'strength100',
                  37949660848, 'gds-native-strength-route'),
    37859526262: ('c2d7c8b1094edd4551cc6078ece502a2758c7255', 'stock125',
                  37853023857, 'gds-native-stock-route'),
    37870374707: ('73a35ce3d22d0b63f213078cdeddc5565f0c1d97', 'hold100',
                  37866086829, 'gds-native-hold100-route'),
}


def validate_relocated(root, run, reviewed_netlist_sha):
    """Prepare relocation GL only after reviewing the completed artifact hash.

    This entry point is intentionally not registered in the dispatch workflow
    until the running experiment completes and its artifact is reviewed.
    Functional GL remains useful even if extracted electrical/timing gates fail.
    """
    if not re.fullmatch(r'[0-9a-f]{64}', reviewed_netlist_sha or ''):
        raise ValueError('Reviewed relocated netlist hash required')
    if (run.get('id') != 37983933655
            or run.get('head_sha') != '0fa2b9f44a06b053142295e41b69d5640e547495'
            or run.get('head_branch') != 'main' or run.get('conclusion') != 'success'
            or run.get('path') != '.github/workflows/gds-sram-relocate-route.yaml'):
        raise ValueError('Relocated routing provenance mismatch')
    route = root / 'runs/native-sram-relocate-route'
    gates = json.loads((route / 'gates.json').read_text())
    if (gates.get('qualified') is not True or gates.get('source_run') != 37978260010
            or gates.get('minimum_fast_hold_ns') != .05
            or gates.get('repair_repeated') is not False
            or gates.get('relocation_repeated') is not False):
        raise ValueError('Relocated pre-route qualification mismatch')
    states = list((route / 'drt').glob('*-openroad-detailedrouting/state_out.json'))
    if len(states) != 1:
        raise ValueError('Exactly one completed relocated DRT checkpoint required')
    step = states[0].parent
    state = json.loads(states[0].read_text())
    suffix = '/runs/native-sram-relocate-route/drt/' + step.name + '/tt_um_tripwire.nl.v'
    if (state.get('metrics', {}).get('route__drc_errors') != 0
            or not str(state.get('nl', '')).endswith(suffix)):
        raise ValueError('Relocated route DRC or netlist identity mismatch')
    config = json.loads((step / 'config.json').read_text())
    recipe = json.loads((root / 'src/config_native_sram_relocate_route.json').read_text())
    for data in (config, recipe):
        if (data.get('CLOCK_PERIOD') != 20 or data.get('GRT_ADJUSTMENT') != .16
                or data.get('GRT_ALLOW_CONGESTION') is not False
                or not str(data.get('PNR_SDC_FILE', '')).endswith('/src/signoff.sdc')):
            raise ValueError('Relocated route configuration mismatch')
    if recipe.get('SYNTH_STRATEGY') != 'AREA 1' or recipe.get('GRT_RESIZER_HOLD_SLACK_MARGIN') != .10:
        raise ValueError('Relocated full recipe mismatch')
    netlist = step / 'tt_um_tripwire.nl.v'
    text = netlist.read_text()
    if 'module tt_um_tripwire' not in text or 'RM_IHPSG13_1P_512x16_c2_bm_bist' not in text:
        raise ValueError('Full-chip SRAM netlist missing')
    digest = hashlib.sha256(netlist.read_bytes()).hexdigest()
    if digest != reviewed_netlist_sha:
        raise ValueError('Relocated routed netlist hash mismatch')
    return dict(netlist=str(netlist), sha256=digest, route_run=run['id'],
                profile='relocated100', functional_simulation_only=True, official_signoff=False)


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
    route_name = 'native-strength-route' if profile == 'strength100' else 'native-stock-route'
    route = root / 'runs' / route_name
    gates = json.loads((route / 'gates.json').read_text())
    if (gates.get('qualified') is not True or (profile != 'strength100' and gates.get('profile') != profile)
            or gates.get('source_run') != source
            or gates.get('minimum_fast_hold_ns') != 0.05):
        raise ValueError('Native pre-route qualification mismatch')
    if profile == 'strength100' and gates.get('repair_repeated') is not False:
        raise ValueError('Strength repair history mismatch')
    states = list((route / 'drt').glob('*-openroad-detailedrouting/state_out.json'))
    if len(states) != 1:
        raise ValueError('Exactly one completed DRT checkpoint required')
    state = json.loads(states[0].read_text())
    if state.get('metrics', {}).get('route__drc_errors') != 0:
        raise ValueError('Native route DRC failure')
    step = states[0].parent
    netlist = step / 'tt_um_tripwire.nl.v'
    suffix = '/runs/' + route_name + '/drt/' + step.name + '/tt_um_tripwire.nl.v'
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
            or recipe.get('GRT_RESIZER_HOLD_SLACK_MARGIN') != (0.10 if profile in ('hold100', 'strength100') else 0.125)
            or not str(recipe.get('PNR_SDC_FILE', '')).endswith('/src/signoff.sdc')):
        raise ValueError('Native full recipe mismatch')
    text = netlist.read_text()
    if ('module tt_um_tripwire' not in text
            or 'RM_IHPSG13_1P_512x16_c2_bm_bist' not in text):
        raise ValueError('Full-chip SRAM netlist missing')
    digest = hashlib.sha256(netlist.read_bytes()).hexdigest()
    if profile == 'strength100' and digest != STRENGTH_NETLIST_SHA:
        raise ValueError('Strength routed netlist hash mismatch')
    return {'netlist': str(netlist), 'sha256': digest,
            'route_run': run['id'], 'profile': profile,
            'functional_simulation_only': True, 'official_signoff': False}

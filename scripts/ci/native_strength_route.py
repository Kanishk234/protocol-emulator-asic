"""Continue the exact qualified six-strength screen without repeating repair."""
import hashlib
import json
import os
import re
from pathlib import Path
from event_nor2_screen import logical_cells, validate_antenna_only_changes, validate_overflow
from native_hold100_size import SOURCE_SHA256, validate_change
from native_stock_route import fingerprints, qualified, run_step
from postgrt_timing import screen

SOURCE_RUN = 37949660848
SOURCE_SHA = 'b6515e5ca22111b5f54489aadf9034cda7d2d266'


def validate_provenance(run, gates):
    if (run.get('id') != SOURCE_RUN or run.get('head_sha') != SOURCE_SHA
            or run.get('head_branch') != 'main' or run.get('conclusion') != 'success'
            or run.get('path') != '.github/workflows/gds-native-hold100-strength-screen.yaml'):
        raise ValueError('Wrong qualified native strength source')
    if (gates.get('source_run') != 37870374707 or gates.get('changes') != 6
            or gates.get('qualified') is not True or gates.get('minimum_fast_hold_ns') != .05
            or gates.get('physical_screen_only') is not True):
        raise ValueError('Wrong native strength qualification gate')


def validate_checkpoint(root):
    timing = json.loads((root / 'timing/comparison.json').read_text())
    state_path = Path(timing['after_state'])
    allowed = [root / 'antenna/1-openroad-checkantennas/state_out.json',
               root / 'antenna-cleanup/2-openroad-checkantennas/eco_state.json']
    if state_path.resolve() not in [p.resolve() for p in allowed]:
        raise ValueError('Wrong native strength checkpoint')
    state = json.loads(state_path.read_text())
    antenna = json.loads((state_path.parent / 'or_metrics_out.json').read_text())
    if not qualified(timing, antenna):
        raise ValueError('Saved native strength timing/hold/antenna gate fails')
    original = Path('runs/extracted-timing/final/nl/tt_um_tripwire.nl.v')
    if hashlib.sha256(original.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError('Wrong original extracted netlist')
    grt = root / 'grt/1-openroad-globalrouting'
    before, after = grt / 'tt_um_tripwire.baseline.nl.v', grt / 'tt_um_tripwire.eco.nl.v'
    if logical_cells(original.read_text()) != logical_cells(before.read_text()):
        raise ValueError('Native sizing baseline mismatch')
    validate_change(before.read_text(), after.read_text())
    validate_antenna_only_changes(after.read_text(), Path(state['nl']).read_text())
    log = (grt / 'openroad-globalrouting.log').read_text()
    if log.count('TRIPWIRE native hold100 setup:') != 6:
        raise ValueError('Wrong native sizing history')
    resets = re.findall(r'TRIPWIRE native route reset: cleared ([0-9]+) ordinary routed wires', log)
    if len(resets) != 1 or int(resets[0]) == 0:
        raise ValueError('Native source lacks detailed-wire reset before GRT')
    validate_overflow(log)
    if 'antenna-cleanup' in state_path.parts:
        cleanup = root / 'antenna-cleanup'
        resolved = json.loads((cleanup / 'resolved.json').read_text())
        logs = list(cleanup.glob('*-openroad-repairantennas/*-openroad-diodeinsertion/openroad-diodeinsertion.log'))
        if (resolved.get('GRT_ALLOW_CONGESTION') is not False or len(logs) != 1
                or 'repair_antennas' not in logs[0].read_text()
                or '-allow_congestion' in logs[0].read_text()):
            raise ValueError('Native cleanup routing policy mismatch')
    for key in ('odb', 'def', 'nl', 'pnl', 'sdc'):
        if not Path(state[key]).is_file():
            raise ValueError('Missing native strength checkpoint ' + key)
    return state_path


def main():
    root = Path('runs/native-hold100-strength')
    validate_provenance(json.loads(Path('/tmp/native-strength-source-run.json').read_text()),
                        json.loads((root / 'gates.json').read_text()))
    expected = json.loads(Path('/tmp/native-trusted-files.json').read_text())
    actual = fingerprints(Path.cwd())
    def hardware(values):
        return {k: v for k, v in values.items()
                if not (k.startswith('src/config') and k.endswith('.json'))}
    if hardware(expected) != hardware(actual):
        raise ValueError('Native route hardware/constraint mismatch')
    original = json.loads(Path('src/config_native_stock.json').read_text())
    if original != json.loads(Path('/tmp/native-trusted-config.json').read_text()):
        raise ValueError('Native route full recipe mismatch')
    config = dict(original, GRT_ALLOW_CONGESTION=False)
    if config != json.loads(Path('src/config_native_hold100_strength.json').read_text()):
        raise ValueError('Native strength physical recipe mismatch')
    if list(root.rglob('*-openroad-detailedrouting')):
        raise ValueError('Strength source already contains detailed routing')
    source = validate_checkpoint(root)
    output = Path('runs/native-strength-route')
    output.mkdir(exist_ok=False)
    os.environ.pop('LIBRELANE_IMAGE_OVERRIDE', None)
    antenna = output / 'antenna'
    run_step(config, source, antenna, ['OpenROAD.CheckAntennas'])
    metrics = list(antenna.glob('*-openroad-checkantennas/or_metrics_out.json'))
    if len(metrics) != 1:
        raise ValueError('Fresh native route antenna evidence missing')
    path = Path('src/config_native_strength_route.json')
    path.write_text(json.dumps(config, indent=2) + '\n')
    screen(path, source, output / 'timing', os.environ['PDK_ROOT'],
           repaired=source, sdc=Path('src/signoff.sdc'))
    timing = json.loads((output / 'timing/comparison.json').read_text())
    ready = qualified(timing, json.loads(metrics[0].read_text()))
    (output / 'gates.json').write_text(json.dumps(dict(source_run=SOURCE_RUN,
        qualified=ready, minimum_fast_hold_ns=.05, repair_repeated=False,
        state=str(source), official_signoff=False), indent=2) + '\n')
    if not ready:
        raise ValueError('Fresh native route timing/50ps hold/antenna gate fails')
    run_step(config, source, output / 'drt', ['OpenROAD.DetailedRouting'])
    Path('src/config_merged.json').write_text(json.dumps(config, indent=2) + '\n')
    # Source contains older extraction. Preserve it, then produce fresh output.
    Path('runs/extracted-timing').rename(output / 'source-extracted-timing')
    from extracted_timing import main as extract
    extract(output / 'drt')


if __name__ == '__main__':
    main()

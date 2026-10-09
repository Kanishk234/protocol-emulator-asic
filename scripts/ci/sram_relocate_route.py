"""Continue the exact qualified SRAM relocation screen without repeating repair."""
import hashlib
import json
import math
import os
import re
from pathlib import Path
from event_nor2_screen import logical_cells, validate_antenna_only_changes
from native_route_gl import STRENGTH_NETLIST_SHA as SOURCE_SHA256
from sram_relocate_screen import validate_history
from native_stock_route import fingerprints, qualified, run_step
from postgrt_timing import CORNERS, screen

SOURCE_RUN = 37978260010
SOURCE_SHA = '815f78cd3423ddffd69374ba4c0e9cc4e849a3ce'


def comparison(before, after):
    result = dict(source_screen=SOURCE_RUN, official_signoff=False, corners={})
    timing_pass = True
    electrical_pass = True
    for corner in CORNERS:
        row = {}
        for label, directory in [('before', before), ('after', after)]:
            timing = json.loads((directory / 'corner_summary.json').read_text())
            electrical = json.loads((directory / 'electrical_summary.json').read_text())[corner]
            setup = timing[f'timing__setup__ws__corner:{corner}']
            hold = timing[f'timing__hold__ws__corner:{corner}']
            row[label] = dict(setup_ns=setup, hold_ns=hold, electrical_counts=electrical['counts'],
                              sram_dout0_cap_violations=[r for r in electrical['violations']['capacitance']
                                                       if r.startswith('u_chip.u_sram.sram/A_DOUT[0] ')])
            if label == 'after':
                timing_pass &= (math.isfinite(setup) and math.isfinite(hold) and setup >= 0
                                and hold >= (.05 if corner == CORNERS[0] else 0))
                electrical_pass &= not any(electrical['counts'][k] for k in ('slew', 'fanout', 'capacitance'))
        result['corners'][corner] = row
    result.update(extracted_timing_qualified=timing_pass, electrical_qualified=electrical_pass)
    return result


def validate_provenance(run, gates):
    if (run.get('id') != SOURCE_RUN or run.get('head_sha') != SOURCE_SHA
            or run.get('head_branch') != 'main' or run.get('conclusion') != 'success'
            or run.get('path') != '.github/workflows/gds-sram-relocate-screen.yaml'):
        raise ValueError('Wrong qualified SRAM relocation source')
    if (gates.get('source_run') != 37954320974 or gates.get('changes') != 0
            or gates.get('relocated_instances') != 1
            or gates.get('qualified') is not True or gates.get('minimum_fast_hold_ns') != .05
            or gates.get('physical_screen_only') is not True):
        raise ValueError('Wrong SRAM relocation qualification gate')


def validate_checkpoint(root):
    timing = json.loads((root / 'timing/comparison.json').read_text())
    state_path = Path(timing['after_state'])
    allowed = [root / 'antenna/1-openroad-checkantennas/state_out.json',
               root / 'antenna-cleanup/2-openroad-checkantennas/eco_state.json']
    if state_path.resolve() not in [p.resolve() for p in allowed]:
        raise ValueError('Wrong SRAM relocation checkpoint')
    state = json.loads(state_path.read_text())
    antenna = json.loads((state_path.parent / 'or_metrics_out.json').read_text())
    if not qualified(timing, antenna):
        raise ValueError('Saved native strength timing/hold/antenna gate fails')
    original = Path('runs/native-strength-route/drt/1-openroad-detailedrouting/tt_um_tripwire.nl.v')
    if hashlib.sha256(original.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError('Wrong original extracted netlist')
    grt = root / 'grt/1-openroad-globalrouting'
    before, after = grt / 'tt_um_tripwire.baseline.nl.v', grt / 'tt_um_tripwire.eco.nl.v'
    if logical_cells(original.read_text()) != logical_cells(before.read_text()):
        raise ValueError('Native sizing baseline mismatch')
    if logical_cells(before.read_text()) != logical_cells(after.read_text()):
        raise ValueError('SRAM relocation changed logic or connections')
    validate_antenna_only_changes(after.read_text(), Path(state['nl']).read_text())
    log = (grt / 'openroad-globalrouting.log').read_text()
    validate_history(log)
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
            raise ValueError('Missing SRAM relocation checkpoint ' + key)
    layout = Path(state['def']).read_text()
    if not re.search(r'wire9447 sg13cmos5l_buf_4[^;]*PLACED [(] 20640 249480 [)] FS', layout):
        raise ValueError('Relocated buffer left audited site after antenna cleanup')
    return state_path


def main():
    root = Path('runs/native-sram-relocate')
    validate_provenance(json.loads(Path('/tmp/sram-relocate-source-run.json').read_text()),
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
    if config != json.loads(Path('src/config_native_sram_relocate.json').read_text()):
        raise ValueError('Native strength physical recipe mismatch')
    if list(root.rglob('*-openroad-detailedrouting')):
        raise ValueError('Strength source already contains detailed routing')
    source = validate_checkpoint(root)
    output = Path('runs/native-sram-relocate-route')
    output.mkdir(exist_ok=False)
    os.environ.pop('LIBRELANE_IMAGE_OVERRIDE', None)
    antenna = output / 'antenna'
    run_step(config, source, antenna, ['OpenROAD.CheckAntennas'])
    metrics = list(antenna.glob('*-openroad-checkantennas/or_metrics_out.json'))
    if len(metrics) != 1:
        raise ValueError('Fresh native route antenna evidence missing')
    path = Path('src/config_native_sram_relocate_route.json')
    path.write_text(json.dumps(config, indent=2) + '\n')
    screen(path, source, output / 'timing', os.environ['PDK_ROOT'],
           repaired=source, sdc=Path('src/signoff.sdc'))
    timing = json.loads((output / 'timing/comparison.json').read_text())
    ready = qualified(timing, json.loads(metrics[0].read_text()))
    (output / 'gates.json').write_text(json.dumps(dict(source_run=SOURCE_RUN,
        qualified=ready, minimum_fast_hold_ns=.05, repair_repeated=False, relocation_repeated=False,
        state=str(source), official_signoff=False), indent=2) + '\n')
    if not ready:
        raise ValueError('Fresh native route timing/50ps hold/antenna gate fails')
    run_step(config, source, output / 'drt', ['OpenROAD.DetailedRouting'])
    Path('src/config_merged.json').write_text(json.dumps(config, indent=2) + '\n')
    # Source contains older extraction. Preserve it, then produce fresh output.
    Path('runs/extracted-timing').rename(output / 'source-extracted-timing')
    from extracted_timing import main as extract
    extract(output / 'drt')
    report = comparison(output / 'source-extracted-timing', Path('runs/extracted-timing'))
    (output / 'extracted_comparison.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()

"""Measure bounded cell choices on fixed extracted RC; no physical repair."""
import hashlib
import json
from pathlib import Path
import re

from event_nor2_screen import logical_cells
from extracted_sizing_sensitivity import sta_input_state, corner_metrics, baseline_matches
from native_stock_route import run_step

TARGETS = {'_27522_': ('sg13cmos5l_nor4_1', 'sg13cmos5l_nor4_2'),
           '_46365_': ('sg13cmos5l_nor4_1', 'sg13cmos5l_nor4_2'),
           'hold11557': ('sg13cmos5l_dlygate4sd3_1', 'sg13cmos5l_dlygate4sd2_1')}
CASES = {'baseline': {}, 'nor4_first': {'_27522_': TARGETS['_27522_'][1]},
         'nor4_last': {'_46365_': TARGETS['_46365_'][1]},
         'nor4_both': {n: TARGETS[n][1] for n in ('_27522_', '_46365_')},
         'delay2': {'hold11557': TARGETS['hold11557'][1]},
         'nor4_both_delay2': {n: pair[1] for n, pair in TARGETS.items()}}


def change_netlist(text, changes):
    original = logical_cells(text)
    result = text
    for name, master in changes.items():
        assert name in TARGETS and master == TARGETS[name][1], 'Unreviewed sizing choice'
        old = TARGETS[name][0]
        assert original.get(name, (None,))[0] == old, 'Wrong original sizing cell'
        pattern = r'\b'+re.escape(old)+r'(\s+)'+re.escape(name)+r'(?=\s*\()'
        result, count = re.subn(pattern, lambda m: master+m[1]+name, result)
        assert count == 1, 'Ambiguous sizing instance'
    expected = dict(original)
    for name, master in changes.items():
        expected[name] = (master, original[name][1])
    assert logical_cells(result) == expected, 'Connectivity or unrelated cell changed'
    return result


def main():
    root = Path('runs/extracted-timing')
    state = json.loads((root/'11-openroad-stapostpnr/state_out.json').read_text())
    reference = json.loads((root/'corner_summary.json').read_text())
    identity = json.loads((root/'constraint_identity.json').read_text())
    sdc = Path(identity['sta_constraint_file'])
    assert hashlib.sha256(sdc.read_bytes()).hexdigest() == identity['sha256']
    assert sdc.read_bytes() == Path('src/signoff.sdc').read_bytes()
    nl = Path(state['nl'])
    paths = [nl, Path(state['odb']), sdc] + [Path(p) for p in state['spef'].values()]
    assert paths and all(p.is_file() for p in paths)
    def hashes():
        return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    source_hashes = hashes()
    text = nl.read_text()
    config = json.loads(Path('src/config_merged.json').read_text())
    assert config['CLOCK_PERIOD'] == 20
    corners = ['nom_fast_1p32V_m40C', 'nom_slow_1p08V_125C', 'nom_typ_1p20V_25C']
    config.update(STA_CORNERS=corners, STA_THREADS=3, SIGNOFF_SDC_FILE=str(sdc.resolve()),
                  STA_EXTRA_CORNER_TCL_FILE=str(Path('scripts/ci/c_select_extracted_frontier.tcl').resolve()))
    output = Path('runs/c-select-extracted-sensitivity')
    output.mkdir(exist_ok=False)
    results = {}
    for name, changes in CASES.items():
        modified = output/(name+'.v')
        modified.write_text(change_netlist(text, changes))
        checkpoint = output/(name+'.json')
        checkpoint.write_text(json.dumps(sta_input_state(state, modified), indent=2)+'\n')
        run_step(config, checkpoint, output/name, ['OpenROAD.STAPostPNR'])
        stages = list((output/name).glob('*-openroad-stapostpnr/state_out.json'))
        assert len(stages) == 1
        measured = corner_metrics(stages[0].parent)
        if name == 'baseline':
            baseline_matches(measured, reference)
        assert hashes() == source_hashes, 'Fixed source views changed'
        results[name] = dict(changes=changes, corners=measured)
        (output/'results.json').write_text(json.dumps(dict(source_run=42252231999,
            baseline_reproduced=True, fixed_spef=True, source_hashes=source_hashes,
            physical_change_applied=False, physical_qualified=False, official_signoff=False,
            cases=results), indent=2)+'\n')
        print(name, json.dumps(measured), flush=True)


if __name__ == '__main__':
    main()

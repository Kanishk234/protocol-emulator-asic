"""Measure bounded cell choices on fixed extracted RC; no physical repair."""
import hashlib
import json
from pathlib import Path
import re

from event_nor2_screen import logical_cells
from extracted_sizing_sensitivity import sta_input_state, corner_metrics, baseline_matches
from native_stock_route import run_step

TARGETS = {'_24522_': ('sg13cmos5l_nand2_1','sg13cmos5l_nand2_2'),
           '_30153_': ('sg13cmos5l_nor3_1','sg13cmos5l_nor3_2'),
           **{n: ('sg13cmos5l_dlygate4sd3_1','sg13cmos5l_dlygate4sd2_1')
              for n in ('hold10767','hold10394','hold10395')}}
GATES = {n: p[1] for n,p in TARGETS.items() if not n.startswith('hold')}
DELAYS = {n: p[1] for n,p in TARGETS.items() if n.startswith('hold')}
CASES = {'baseline': {}, **{n:{n:m} for n,m in GATES.items()},
         'gates': GATES, 'delays': DELAYS, 'combined': {**GATES, **DELAYS}}


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
    from official_dev4_cpad_route import verify_source, bootstrap_ciel_antenna
    source, config = verify_source()
    bootstrap_ciel_antenna(config, source, output_name='cpad-audit-pdk')
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
    assert hashlib.sha256(nl.read_bytes()).hexdigest() == '3bf46dca904b867b0c9c5a7ddd7e508d3c7e5ec0ac03d637d0262277a61b8639'
    text = nl.read_text()
    config = json.loads(Path('src/config_merged.json').read_text())
    assert config['CLOCK_PERIOD'] == 20
    corners = ['nom_fast_1p32V_m40C', 'nom_slow_1p08V_125C', 'nom_typ_1p20V_25C']
    config.update(STA_CORNERS=corners, STA_THREADS=3, SIGNOFF_SDC_FILE=str(sdc.resolve()),
                  STA_EXTRA_CORNER_TCL_FILE=str(Path('scripts/ci/cpad_endpoint_audit.tcl').resolve()))
    output = Path('runs/cpad-endpoint-audit')
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
        (output/'results.json').write_text(json.dumps(dict(source_run=43063738642,
            baseline_reproduced=True, fixed_spef=True, source_hashes=source_hashes,
            physical_change_applied=False, physical_qualified=False, official_signoff=False,
            cases=results), indent=2)+'\n')
        print(name, json.dumps(measured), flush=True)


if __name__ == '__main__':
    main()

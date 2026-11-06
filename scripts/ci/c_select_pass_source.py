"""Restore only the exact green C-selector checkpoint; never repeat repairs."""
import hashlib
import json
import math
from pathlib import Path
import re
import shutil

CORNERS = ('nom_fast_1p32V_m40C', 'nom_slow_1p08V_125C', 'nom_typ_1p20V_25C')


def require_gates(gates):
    assert gates.get('edited') is True and gates.get('diagnostic_gates_passed') is True
    assert gates.get('failures') == [] and type(gates.get('overflow')) is int and gates['overflow'] == 0
    assert gates.get('antenna') == {'antenna__violating__nets': 0, 'antenna__violating__pins': 0}
    assert all(type(value) is int for value in gates['antenna'].values())
    assert set(gates['corners']) == set(CORNERS)
    for corner in CORNERS:
        row = gates['corners'][corner]
        for kind in ('setup', 'hold'):
            value = row[f'timing__{kind}__ws__corner:{corner}']
            minimum = .05 if kind == 'hold' and corner == CORNERS[0] else 0
            assert type(value) in (int, float) and math.isfinite(value) and value >= minimum
        for kind in ('slew', 'cap', 'fanout'):
            value = row[f'design__max_{kind}_violation__count__corner:{corner}']
            assert type(value) is int and value == 0


def restore(root, manifest, run, artifact):
    root = Path(root).resolve()
    for name, actual in (('run', run), ('artifact', artifact)):
        assert all(actual.get(k) == v for k, v in manifest[name].items()), 'Wrong passing source provenance'
    for name, digest in manifest['files'].items():
        path = root / name
        assert not Path(name).is_absolute() and path.resolve().is_relative_to(root)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, 'Passing source hash mismatch: ' + name
    base = root / 'runs/route-reopen-calibration'
    read = lambda name: json.loads((root / name).read_text())
    gates = read('runs/route-reopen-calibration/final_gates.json')
    require_gates(gates)
    coverage = read('runs/route-reopen-calibration/native_coverage.json')
    assert coverage['all_routed_nets_connected_and_pins_covered'] is True
    assert coverage['independent_process'] is True and coverage['exact_route_roundtrip'] is True
    assert coverage['routed_nets'] == 44792
    assert read('runs/route-reopen-calibration/geometry_result.json')['exact_roundtrip'] is True
    signoff = read('runs/c-select-signoff-audit/qualification.json')
    assert signoff['qualified'] is True and signoff['failures'] == [] and signoff['edited'] is True
    intervention = read('runs/route-reopen-calibration/intervention.json')
    for key in ('placement_checked', 'post_router_placement_checked', 'original_clock_route_preserved'):
        assert intervention[key] is True
    assert intervention['original_data_routes_preserved'] == ['_02001_', 'u_chip.g_lane[1].ot[26]']
    assert len(intervention['reviewed_via_attachments']) == 2
    log = (root / 'runs/route-reopen.log').read_text()
    assert not re.search(r'(?m)^\[ERROR\b', log)
    totals = re.findall(r'(?m)^Total\s+\d+\s+(\d+)\s+[0-9.]+%\s+\d+\s*/\s*\d+\s*/\s*(\d+)\s*$', log)
    assert totals and int(totals[-1][0]) > 0 and int(totals[-1][1]) == 0
    state = json.loads((base / 'state_out.json').read_text())
    for key in ('odb', 'def', 'nl', 'pnl'):
        expected = Path.cwd() / 'runs/route-reopen-calibration' / ('calibrated.' + {'nl': 'nl.v', 'pnl': 'pnl.v'}.get(key, key))
        assert Path(state[key]) == expected, 'Wrong measured state view: ' + key
    sdc = Path(state['sdc'])
    assert sdc.is_file() and hashlib.sha256(sdc.read_bytes()).hexdigest() == manifest['sdc_sha256']
    target = Path('runs/route-reopen-calibration')
    assert not target.exists(), 'Refusing existing continuation input'
    shutil.copytree(base, target)
    shutil.copy2(root / 'runs/route-reopen.log', 'runs/route-reopen.log')
    # Coverage is revalidated independently, not inherited from the source.
    (target / 'native_coverage.json').unlink()
    (target / 'coverage-readback.segments').unlink(missing_ok=True)
    Path('runs/c-select-pass-restoration.json').write_text(json.dumps(dict(
        source_run=run['id'], source_sha=run['head_sha'], artifact_id=artifact['id'],
        checkpoint_state=str(target / 'state_out.json'), physical_repairs_repeated=False,
        bound_files=manifest['files'], official_flow_qualified=False), indent=2) + '\n')

import copy
import hashlib
import json
from pathlib import Path

import pytest

from c_select_pass_source import CORNERS, require_gates, restore


def fixture():
    corners = {}
    for corner in CORNERS:
        row = {f'timing__{kind}__ws__corner:{corner}': .1 for kind in ('setup', 'hold')}
        row.update({f'design__max_{kind}_violation__count__corner:{corner}': 0 for kind in ('slew', 'cap', 'fanout')})
        corners[corner] = row
    return dict(edited=True, diagnostic_gates_passed=True, failures=[], overflow=0,
                antenna={'antenna__violating__nets': 0, 'antenna__violating__pins': 0}, corners=corners)


def test_strict_green_source_accepts():
    require_gates(fixture())


@pytest.mark.parametrize('fault', ['control', 'unqualified', 'failure', 'overflow', 'antenna',
                                 'corner', 'setup', 'hold', 'margin', 'nan', 'electrical'])
def test_partial_or_invalid_source_refused(fault):
    gates = fixture()
    if fault == 'control': gates['edited'] = False
    elif fault == 'unqualified': gates['diagnostic_gates_passed'] = False
    elif fault == 'failure': gates['failures'] = ['failure']
    elif fault == 'overflow': gates['overflow'] = 1
    elif fault == 'antenna': gates['antenna']['antenna__violating__pins'] = 1
    elif fault == 'corner': gates['corners'].pop(CORNERS[1])
    elif fault == 'electrical': gates['corners'][CORNERS[0]][f'design__max_slew_violation__count__corner:{CORNERS[0]}'] = 1
    else:
        kind = 'setup' if fault == 'setup' else 'hold'
        gates['corners'][CORNERS[0]][f'timing__{kind}__ws__corner:{CORNERS[0]}'] = (
            float('nan') if fault == 'nan' else .049 if fault == 'margin' else -.01)
    with pytest.raises(AssertionError):
        require_gates(gates)


@pytest.mark.parametrize('fault', [None, 'run', 'hash', 'coverage', 'state', 'sdc'])
def test_exact_restore_or_refusal_before_copy(tmp_path, monkeypatch, fault):
    monkeypatch.chdir(tmp_path)
    root = Path('passing')
    base = root / 'runs/route-reopen-calibration'
    base.mkdir(parents=True)
    Path('runs').mkdir()
    Path('constraints.sdc').write_text('clock20')
    state = {'sdc': str(Path('constraints.sdc').resolve())}
    for key, suffix in (('odb','odb'),('def','def'),('nl','nl.v'),('pnl','pnl.v')):
        state[key] = str(Path('runs/route-reopen-calibration', 'calibrated.'+suffix).resolve())
        (base / ('calibrated.'+suffix)).write_text(key)
    if fault == 'state': state['odb'] = '/wrong.odb'
    def write(name, data):
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(data))
    write('runs/route-reopen-calibration/state_out.json',state)
    write('runs/route-reopen-calibration/final_gates.json',fixture())
    write('runs/route-reopen-calibration/geometry_result.json',{'exact_roundtrip':True})
    write('runs/route-reopen-calibration/native_coverage.json',dict(
        all_routed_nets_connected_and_pins_covered=fault!='coverage', independent_process=True,
        exact_route_roundtrip=True,routed_nets=44792))
    write('runs/c-select-signoff-audit/qualification.json',dict(qualified=True,failures=[],edited=True))
    write('runs/route-reopen-calibration/intervention.json',dict(placement_checked=True,
        post_router_placement_checked=True,original_clock_route_preserved=True,
        original_data_routes_preserved=['_02001_','u_chip.g_lane[1].ot[26]'],reviewed_via_attachments=[{},{}]))
    (root/'runs/route-reopen.log').write_text('Total 100 10 10.0% 0 / 0 / 0\n')
    manifest=dict(run={'id':1},artifact={'id':2},files={
        str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob('*') if p.is_file()},
        sdc_sha256=hashlib.sha256(Path('constraints.sdc').read_bytes()).hexdigest())
    if fault=='hash': (base/'calibrated.odb').write_text('corrupt')
    if fault=='sdc': Path('constraints.sdc').write_text('relaxed')
    if fault:
        with pytest.raises(AssertionError):
            restore(root,manifest,{'id':0 if fault=='run' else 1,'head_sha':'tested'},{'id':2})
        assert not Path('runs/route-reopen-calibration').exists()
    else:
        restore(root,manifest,{'id':1,'head_sha':'tested'},{'id':2})
        assert Path('runs/route-reopen-calibration/calibrated.odb').read_text()=='odb'
        assert not Path('runs/route-reopen-calibration/native_coverage.json').exists()

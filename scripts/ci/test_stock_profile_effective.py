import json

import pytest

from stock_profile_effective import validate


def fixture(root, changes, *, density=61, wire=400, late=None, reroute=True, diode=False, adjustment=16):
    config = dict(PL_TARGET_DENSITY_PCT=56, GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH=wire,
                  RUN_POST_GRT_RESIZER_TIMING=False, GRT_RESIZER_HOLD_SLACK_MARGIN=0.125,
                  GRT_RESIZER_RUN_GRT=reroute, GRT_ADJUSTMENT=0.16,
                  GRT_LAYER_ADJUSTMENTS=[0, 0, 0, 0, 0],
                  GRT_ANTENNA_REPAIR_DIODE_ONLY=False)
    config.update(changes)
    (root / 'resolved.json').write_text(json.dumps(config))
    gpl = root / '28-openroad-globalplacement'
    gpl.mkdir()
    (gpl / 'openroad-globalplacement.log').write_text(f'Placement target density: {density/100:.4f}\n')
    repair = root / '41-openroad-repairdesignpostgrt'
    repair.mkdir()
    (repair / 'openroad-repairdesignpostgrt.log').write_text(f'+ repair_design -verbose -max_wire_length {wire}.0 -slew_margin 10.0\n')
    if late is not None:
        repair = root / '44-openroad-resizertimingpostgrt'
        repair.mkdir()
        (repair / 'state_out.json').write_text('{}')
        (repair / 'openroad-resizertimingpostgrt.log').write_text(f'[INFO GRT-0022] Global adjustment: {adjustment}%\n+ repair_timing -verbose -hold -setup_margin 0 -hold_margin {late} -max_buffer_percent 50\n')
    repair = root / '43-openroad-repairantennas/1-openroad-diodeinsertion'
    repair.mkdir(parents=True)
    (repair / 'openroad-diodeinsertion.log').write_text('+ repair_antennas cell -iterations 3 -ratio_margin 10' + (' -diode_only' if diode else '') + '\n')
    return dict(profile='test', changes=changes)


def test_wire_control_exercised(tmp_path):
    selected = fixture(tmp_path, dict(GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH=400))
    assert validate(tmp_path, selected)['native_max_wire_length_um'] == 400


def test_density_clamp_rejected(tmp_path):
    selected = fixture(tmp_path, dict(PL_TARGET_DENSITY_PCT=54))
    with pytest.raises(ValueError, match='clamped'):
        validate(tmp_path, selected)


def test_resolved_mismatch(tmp_path):
    selected = fixture(tmp_path, dict(GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH=400))
    selected['changes']['GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH'] = 500
    with pytest.raises(ValueError, match='Resolved profile mismatch'):
        validate(tmp_path, selected)


def test_wire_command_mismatch(tmp_path):
    selected = fixture(tmp_path, dict(GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH=400), wire=300)
    with pytest.raises(ValueError, match='not exercised'):
        validate(tmp_path, selected)


def test_late_control_exercised(tmp_path):
    selected = fixture(tmp_path, dict(RUN_POST_GRT_RESIZER_TIMING=True,
                                    GRT_RESIZER_HOLD_SLACK_MARGIN=0.075), late=0.075)
    assert validate(tmp_path, selected)['native_late_hold_target_ns'] == 0.075


def test_missing_late_step(tmp_path):
    selected = fixture(tmp_path, dict(RUN_POST_GRT_RESIZER_TIMING=True,
                                    GRT_RESIZER_HOLD_SLACK_MARGIN=0.075))
    with pytest.raises(ValueError, match='Expected one'):
        validate(tmp_path, selected)


def test_late_target_mismatch(tmp_path):
    selected = fixture(tmp_path, dict(RUN_POST_GRT_RESIZER_TIMING=True,
                                    GRT_RESIZER_HOLD_SLACK_MARGIN=0.075), late=0.125)
    with pytest.raises(ValueError, match='not exercised'):
        validate(tmp_path, selected)


def test_late_reroute_cannot_be_disabled(tmp_path):
    selected = fixture(tmp_path, dict(RUN_POST_GRT_RESIZER_TIMING=True,
                                    GRT_RESIZER_HOLD_SLACK_MARGIN=0.075), late=0.075, reroute=False)
    with pytest.raises(ValueError, match='rerouting must remain enabled'):
        validate(tmp_path, selected)


def test_diode_mode_command_verified(tmp_path):
    selected = fixture(tmp_path, dict(GRT_ANTENNA_REPAIR_DIODE_ONLY=True), diode=True)
    assert validate(tmp_path, selected)['native_antenna_mode'] == 'diode_only'


def test_diode_mode_noop_rejected(tmp_path):
    selected = fixture(tmp_path, dict(GRT_ANTENNA_REPAIR_DIODE_ONLY=True))
    with pytest.raises(ValueError, match='not exercised'):
        validate(tmp_path, selected)


def test_routing_reserve_command_verified(tmp_path):
    selected = fixture(tmp_path, dict(RUN_POST_GRT_RESIZER_TIMING=True,
                                    GRT_RESIZER_HOLD_SLACK_MARGIN=0.075,
                                    GRT_ADJUSTMENT=0.15), late=0.075, adjustment=15)
    assert validate(tmp_path, selected)['native_global_adjustment'] == 0.15


def test_routing_reserve_noop_rejected(tmp_path):
    selected = fixture(tmp_path, dict(RUN_POST_GRT_RESIZER_TIMING=True,
                                    GRT_RESIZER_HOLD_SLACK_MARGIN=0.075,
                                    GRT_ADJUSTMENT=0.15), late=0.075)
    with pytest.raises(ValueError, match='not exercised'):
        validate(tmp_path, selected)


@pytest.mark.parametrize('key,command,flag,step,filename,value', [
    ('GRT_ANTENNA_REPAIR_MARGIN', 'repair_antennas', '-ratio_margin',
     '43-openroad-repairantennas/1-openroad-diodeinsertion', 'openroad-diodeinsertion.log', 50),
    ('PL_RESIZER_HOLD_SLACK_MARGIN', 'repair_timing', '-hold_margin',
     '37-openroad-resizertimingpostcts', 'openroad-resizertimingpostcts.log', 0.175),
])
@pytest.mark.parametrize('matches', [True, False])
def test_native_repair_target_verified(tmp_path, key, command, flag, step, filename, value, matches):
    selected = fixture(tmp_path, {key: value})
    path = tmp_path / step / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    actual = value if matches else value + 1
    path.write_text(f'+ {command} {flag} {actual}\n')
    if matches:
        validate(tmp_path, selected)
    else:
        with pytest.raises(ValueError, match='not exercised'):
            validate(tmp_path, selected)

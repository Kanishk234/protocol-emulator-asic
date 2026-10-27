import json

import pytest

from stock_profile_effective import validate


def fixture(root, changes, *, density=61, wire=400, late=None, reroute=True):
    config = dict(PL_TARGET_DENSITY_PCT=56, GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH=wire,
                  RUN_POST_GRT_RESIZER_TIMING=False, GRT_RESIZER_HOLD_SLACK_MARGIN=0.125,
                  GRT_RESIZER_RUN_GRT=reroute)
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
        (repair / 'openroad-resizertimingpostgrt.log').write_text(f'+ repair_timing -verbose -hold -setup_margin 0 -hold_margin {late} -max_buffer_percent 50\n')
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

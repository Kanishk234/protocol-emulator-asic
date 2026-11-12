import json

import pytest

from drive2_mixed_antenna import prepare
from min_drive_profile import prepare as prepare_drive
from stock_profile_effective import validate
from test_min_drive_profile import prepared
from test_stock_profile_effective import fixture


def test_only_native_antenna_policy_changes(tmp_path):
    prepared(tmp_path)
    prepare_drive(tmp_path)
    path=tmp_path/'src/config.json'
    before=json.loads(path.read_text())
    receipt=prepare(tmp_path)
    after=json.loads(path.read_text())
    assert {k:v for k,v in after.items() if before.get(k)!=v} == {'GRT_ANTENNA_REPAIR_DIODE_ONLY':False}
    assert after['CLOCK_PERIOD']==20 and after['GRT_RESIZER_HOLD_SLACK_MARGIN']==.125
    assert receipt['physical_qualified'] is False
    with pytest.raises(ValueError, match='Wrong native-drive configuration'):
        prepare(tmp_path)


@pytest.mark.parametrize('actual', ['mixed','diode','jumper'])
def test_actual_native_command_is_checked(tmp_path, actual):
    selected=fixture(tmp_path, {'GRT_ANTENNA_REPAIR_DIODE_ONLY':False})
    p=tmp_path/'43-openroad-repairantennas/1-openroad-diodeinsertion/openroad-diodeinsertion.log'
    flag={'mixed':'','diode':' -diode_only','jumper':' -jumper_only'}[actual]
    p.write_text('+ repair_antennas cell -iterations 3'+flag+'\n')
    if actual=='mixed':
        assert validate(tmp_path,selected)['native_antenna_mode']=='mixed'
    else:
        with pytest.raises(ValueError,match='mixed antenna'):
            validate(tmp_path,selected)

import json
import pytest

from drive2_wire175 import prepare
from min_drive_profile import prepare as prepare_drive
from test_min_drive_profile import prepared


def test_wire_target_is_the_only_change(tmp_path):
    prepared(tmp_path)
    prepare_drive(tmp_path)
    p=tmp_path/'src/config.json'
    before=json.loads(p.read_text())
    result=prepare(tmp_path)
    after=json.loads(p.read_text())
    assert {k:v for k,v in after.items() if before.get(k)!=v} == {'GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH':175}
    assert after['CLOCK_PERIOD']==20
    assert after['GRT_ANTENNA_REPAIR_DIODE_ONLY'] is True
    assert after['GRT_RESIZER_HOLD_SLACK_MARGIN']==.125
    assert result['changed_fields']==['GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH']
    with pytest.raises(ValueError,match='configuration'):
        prepare(tmp_path)


def test_other_recipe_is_rejected_without_mutation(tmp_path):
    prepared(tmp_path)
    p=tmp_path/'src/config.json'
    before=p.read_bytes()
    with pytest.raises(ValueError,match='configuration'):
        prepare(tmp_path)
    assert p.read_bytes()==before

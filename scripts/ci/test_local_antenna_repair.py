import copy
import pytest
from local_antenna_repair import audit_snapshot


def fixture():
    before = {n: dict(master='buf2', location=(0, 0), orientation='R0', status='PLACED', pins={'A': 'a', 'X': 'b'}) for n in ('sized', 'untouched')}
    after = copy.deepcopy(before)
    after['sized']['master'] = 'buf4'
    after['sized']['location'] = (10, 0)
    after['tripwire_local_diode'] = {}
    return before, after


def test_bounded_change_accepts():
    audit_snapshot(*fixture(), {'sized'}, {'sized': 'buf4'})


@pytest.mark.parametrize('field,value', [('location', (1, 0)), ('orientation', 'MX'), ('status', 'LOCKED'), ('master', 'buf8'), ('pins', {'A': 'wrong'})])
def test_unrelated_change_rejects(field, value):
    before, after = fixture()
    after['untouched'][field] = value
    with pytest.raises(AssertionError):
        audit_snapshot(before, after, {'sized'}, {'sized': 'buf4'})


def test_changed_target_connection_rejects():
    before, after = fixture()
    after['sized']['pins']['A'] = 'wrong'
    with pytest.raises(AssertionError):
        audit_snapshot(before, after, {'sized'}, {'sized': 'buf4'})

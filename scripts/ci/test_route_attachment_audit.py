import copy
import hashlib
import json

import pytest

from route_attachment_audit import REVIEWED, atomic_routes, validate_plan, verify_loaded
from route_segment_audit import parse


def fixture():
    attachments = [dict(net=n, point_dbu=p.copy()) for n, p in REVIEWED]
    source = ''
    edited = ''
    for net, (x, y) in REVIEWED:
        segments = f'{x} {y-7200} Metal2 {x} {y+7200} Metal2\n'
        source += f'{net}\n(\n{segments})\n'
        edited += (f'{net}\n(\n{x} {y-7200} Metal2 {x} {y} Metal2\n'
                   f'{x} {y} Metal2 {x} {y+7200} Metal2\n'
                   f'{x} {y} Metal1 {x} {y} Metal2\n)\n')
    reference = dict(atomic_route_sha256=hashlib.sha256(json.dumps(
        atomic_routes(parse(source)), sort_keys=True, separators=(',', ':')).encode()).hexdigest())
    return edited, reference, attachments


def test_only_reviewed_vias_and_segment_splits_accept():
    verify_loaded(*fixture())


@pytest.mark.parametrize('fault', ['missing', 'duplicate', 'moved', 'extra_track', 'disconnected'])
def test_missing_extra_or_disconnected_geometry_rejects(fault):
    text, reference, attachments = fixture()
    x, y = REVIEWED[0][1]
    via = f'{x} {y} Metal1 {x} {y} Metal2\n'
    if fault == 'missing':
        text = text.replace(via, '')
    elif fault == 'duplicate':
        text = text.replace(via, via+via)
    elif fault == 'moved':
        text = text.replace(via, via.replace(str(x), str(x+7200)))
    elif fault == 'extra_track':
        text = text.replace(via, via+f'{x} {y} Metal3 {x+7200} {y} Metal3\n')
    else:
        text = text.replace(f'{x} {y-7200} Metal2 {x} {y} Metal2\n', '')
        text = text.replace(f'{x} {y} Metal2 {x} {y+7200} Metal2\n', '')
    with pytest.raises(AssertionError):
        verify_loaded(text, reference, attachments)


def test_atomic_geometry_retains_duplicate_tracks():
    route = ((0, 0, 'Metal2'), (0, 14400, 'Metal2'))
    assert len(atomic_routes({'x': [route]})['x']) == 2
    assert len(atomic_routes({'x': [route, route]})['x']) == 4


def test_unreviewed_attachment_plan_rejects():
    _, _, attachments = fixture()
    wrong = copy.deepcopy(attachments)
    wrong[0]['point_dbu'][0] += 7200
    with pytest.raises(AssertionError):
        validate_plan(wrong)

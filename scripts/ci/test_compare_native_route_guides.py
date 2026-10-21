import hashlib

import pytest

from compare_native_route_guides import bounds, compare
from native_lane_mask_stage_probe import PROFILE
from native_no_final_grt_control import SOURCE_ODB_HASH


def test_bounds():
    assert bounds('_n_\n(\n10 20 30 40 Metal2\n0 30 20 70 Metal3\n)\n', '_n_') == {
        'rectangles': 2, 'bbox_dbu': [0, 20, 30, 70]}


@pytest.mark.parametrize('body', ['', '1 2 3 Metal2', '3 2 1 4 Metal2'])
def test_invalid_bounds(body):
    with pytest.raises(ValueError):
        bounds('_n_\n(\n'+body+'\n)\n', '_n_')


def test_provenance_and_hash():
    data = ''.join(n+'\n(\n0 0 10 10 Metal2\n)\n' for n in PROFILE['nets']).encode()
    receipt = dict(source_run=PROFILE['source_run'], source_sha=PROFILE['source_sha'],
        source_odb_sha256=SOURCE_ODB_HASH, diagnostic_only=True, qualified=False,
        native_final_reroute=True, snapshots={s: {'after_grt.guide': {
            'sha256': hashlib.sha256(data).hexdigest()}} for s in ('initial_route', 'final_route')})
    assert compare(receipt, data, data)['qualified'] is False
    with pytest.raises(ValueError, match='bytes'):
        compare(receipt, data+b' ', data)
    with pytest.raises(ValueError, match='provenance'):
        compare(dict(receipt, source_run=0), data, data)

from copy import deepcopy
import pytest
from profiling.r1_registered_input import park_words,admit_timing_result


def change():
    return dict(tile_bit=183,frame=5,data_bit=23,tile='Tile_X2Y3_LUT4x8_ha',before='0',after='1')


def test_candidate_changes_exactly_one_data_bit_and_preserves_parent():
    parent=[0]*962;candidate=park_words(parent,change())
    assert sum((a^b).bit_count() for a,b in zip(parent,candidate))==1
    assert candidate[273]==1<<23 and not any(parent)
    with pytest.raises(ValueError,match='already set'):park_words(candidate,change())
    with pytest.raises(ValueError):park_words(parent[:-1],change())
    bad=change();bad['tile_bit']=184
    with pytest.raises(ValueError):park_words(parent,bad)


def test_actual_image_requires_supported_matching_timing_measurement():
    row=dict(diagnostic_complete=True,hypothesis_supported=True,change=change(),observations={
        'control':dict(loop_policy_differences=[{}]*6),
        'candidate':dict(loop_policy_sensitive=False,loop_policy_differences=[],worst_slack_ns=1.5)})
    admit_timing_result(row,change())
    for fault in ('unsupported','sensitive','negative','changed'):
        bad=deepcopy(row)
        if fault=='unsupported':bad['hypothesis_supported']=False
        if fault=='sensitive':bad['observations']['candidate']['loop_policy_sensitive']=True
        if fault=='negative':bad['observations']['candidate']['worst_slack_ns']=-0.1
        if fault=='changed':bad['change']['tile_bit']=184
        with pytest.raises(ValueError):admit_timing_result(bad,change())


def test_loaded_candidate_must_match_exactly_the_analyzed_bit_and_shell():
    from profiling.r1_registered_input import audit_snapshots
    parent={'tiles':{f't{i}':dict(tile_type='dummy',q={}) for i in range(39)}}
    parent['tiles']['Tile_X2Y3_LUT4x8_ha']=dict(tile_type='LUT4x8_ha',q={'_1560_':'0','other':'1'})
    candidate=deepcopy(parent);candidate['tiles']['Tile_X2Y3_LUT4x8_ha']['q']['_1560_']='1'
    assert audit_snapshots(parent,candidate,candidate)['analysis_case_matches_loaded_candidate']
    bad=deepcopy(candidate);bad['tiles']['Tile_X2Y3_LUT4x8_ha']['q']['other']='0'
    with pytest.raises(ValueError):audit_snapshots(parent,bad,bad)
    with pytest.raises(ValueError):audit_snapshots(parent,candidate,parent)

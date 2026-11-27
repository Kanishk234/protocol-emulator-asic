"""Refuse unknown/conflicting observations before using physical spare routes."""
from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from capture_spare_inputs import runtime_values,terminal_value,prepare


def test_runtime_bit_aliases_must_agree_and_have_matching_width():
    flat={'cells':{'Tile_X1Y1_K/a':{'connections':{'A':[2],'X':[3]}},
                   'Tile_X1Y1_K/b':{'connections':{'A':[3]}}}}
    row={'type':'sg13cmos5l_buf_1','pins':{'A':'0','X':'1'}}
    runtime={'tiles':{'Tile_X1Y1_K':{'cells':{'a':row,'b':{'type':'sg13cmos5l_buf_1','pins':{'A':'1'}}}}}}
    assert runtime_values(flat,runtime)=={2:'0',3:'1'}
    runtime['tiles']['Tile_X1Y1_K']['cells']['b']['pins']['A']='0'
    with pytest.raises(ValueError,match='Conflicting'):runtime_values(flat,runtime)
    runtime['tiles']['Tile_X1Y1_K']['cells']['b']['pins']['A']='00'
    with pytest.raises(ValueError,match='width'):runtime_values(flat,runtime)


def test_terminal_requires_actual_defined_scalar_observation():
    state={'tiles':{'Tile_X1Y1_K':{}}};flat={'netnames':{
        'Tile_X1Y1_K/A_OUT_top':{'bits':[2]},'Tile_X1Y1_K/SA_q':{'bits':list(range(10,18))}}}
    assert terminal_value(flat,{2:'1'},state,'X1Y1','A_OUT')=='1'
    assert terminal_value(flat,{12:'0'},state,'X1Y1','SA_q2')=='0'
    for values in ({},{2:'X'},{2:'Z'}):
        with pytest.raises(ValueError,match='observed-defined'):terminal_value(flat,values,state,'X1Y1','A_OUT')


def test_failed_parent_cannot_stage_spare_input_changes(tmp_path):
    import json
    p=tmp_path/'source/sa_functional';p.mkdir(parents=True)
    (p/'result.json').write_text(json.dumps({'run':'wrong','source_sha':'wrong','passed':False}))
    t=tmp_path/'source/r1_loop_timing';t.mkdir()
    (t/'result.json').write_text('{}')
    with pytest.raises(ValueError,match='exact native'):
        prepare(tmp_path/'capsule',tmp_path/'native',tmp_path/'trial',tmp_path/'source',tmp_path/'out')
    assert not (tmp_path/'out').exists()

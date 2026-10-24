import io
import pickle
import pytest
from compile.bitgen import words
from profiling.r1_quiesce import ground_unused, PlainSpec


def fixture():
    spec={'ArchSpecs':{'MaxFramesPerCol':1,'FrameBitsPerRow':32},
          'TileMap':{'X0Y0':'T'},'TileSpecs':{'X0Y0':{
              'A.UNUSED':{0:'0',1:'0'},'B.UNUSED':{0:'1',1:'0'},'C.UNUSED':{0:'0',1:'1'},
              'A.ACTIVE':{2:'0',3:'0'},'B.ACTIVE':{2:'1',3:'0'},'C.ACTIVE':{2:'0',3:'1'}}}}
    text='cus_mux41 inst_cus_mux41_UNUSED (.A3(GND0),.X(UNUSED));\ncus_mux41 inst_cus_mux41_ACTIVE (.A3(GND0),.X(ACTIVE));'
    features=['X0Y0.B.ACTIVE']
    return spec,features,{'T':text}


def test_only_unused_existing_ground_padding_changes_and_frames_are_preserved():
    spec,features,switches=fixture();before=words(features,spec)
    after,changes=ground_unused(before,spec,features,switches)
    assert changes==[{'tile':'X0Y0','output':'UNUSED','padding_slot':3,'tile_bits':[0,1]}]
    assert after[2]==before[2]|3 and after[:2]==before[:2] and after[3:]==before[3:]
    assert after[2]&12==before[2]&12


def test_active_groundable_output_and_non_ground_padding_are_never_overridden():
    spec,features,switches=fixture()
    features.append('X0Y0.A.UNUSED');before=words(features,spec)
    assert ground_unused(before,spec,features,switches)==(before,[])
    features.pop();before=words(features,spec)
    assert ground_unused(before,spec,features,{'T':switches['T'].replace('GND0','VCC0')})==(before,[])


def test_full_selector_source_is_not_treated_as_padding():
    spec,features,switches=fixture()
    spec['TileSpecs']['X0Y0']['D.UNUSED']={0:'1',1:'1'}
    before=words(features,spec)
    assert ground_unused(before,spec,features,switches)==(before,[])


def test_mismatched_original_or_active_bit_collision_is_rejected():
    spec,features,switches=fixture();before=words(features,spec);before[2]^=1
    with pytest.raises(ValueError,match='reproduce'):ground_unused(before,spec,features,switches)
    for feature in ('A.ACTIVE','B.ACTIVE','C.ACTIVE'):
        spec['TileSpecs']['X0Y0'][feature]=dict(spec['TileSpecs']['X0Y0'][feature],**{})
        spec['TileSpecs']['X0Y0'][feature][0]='0'
    with pytest.raises(ValueError,match='overlaps'):ground_unused(words(features,spec),spec,features,switches)


def test_plain_spec_refuses_executable_pickle_globals():
    assert PlainSpec(io.BytesIO(pickle.dumps({'plain':[1,'0']}))).load()=={'plain':[1,'0']}
    with pytest.raises(ValueError,match='Executable'):PlainSpec(io.BytesIO(pickle.dumps(eval))).load()

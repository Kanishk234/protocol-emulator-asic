import importlib.util
from pathlib import Path
import pickle
import pytest

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('r1_generator', ROOT/'spikes/r1/qualify_generator.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


@pytest.fixture
def control(tmp_path):
    new, old = tmp_path/'new', tmp_path/'old'
    new.mkdir(); (old/'.FABulous').mkdir(parents=True)
    for name, text in {'pips.txt':'X1Y1,a,X1Y1,b,8,a.b\n', 'bel.txt':'a,b,c\n', 'bel.v2.txt':'a,b,c,d\n'}.items():
        (new/name).write_text(text)
        (old/'.FABulous'/name).write_text(text)
    before = dict(TileMap={'X1Y1':'LUT'}, TileSpecs={'x':{'f':{0:'1'}}}, ArchSpecs={'MaxFramesPerCol':20,'FrameBitsPerRow':32})
    after = dict(before, ArchSpecs=dict(before['ArchSpecs'], **m.EXTRA_ARCH))
    (new/'bitStreamSpec.bin').write_bytes(pickle.dumps(after))
    (old/'bitStreamSpec.bin').write_bytes(pickle.dumps(before))
    return new, old


def test_exact_control_maps_and_explicit_timing_scope(control):
    result=m.compare_control(*control)
    assert result['configuration_maps_equal'] and result['graph_records']['pips.txt']==1
    assert not result['pip_delays_qualified'] and not result['physical_acceptance']


def test_delay_change_is_not_graph_change(control):
    new, old=control
    (new/'pips.txt').write_text('X1Y1,a,X1Y1,b,123,a.b\n')
    assert m.compare_control(new,old)['configuration_maps_equal']


@pytest.mark.parametrize('name', ['pips.txt','bel.txt','bel.v2.txt'])
def test_missing_or_duplicated_record_rejected(control,name):
    new,old=control
    original=(new/name).read_text()
    for value in ('',original*2):
        (new/name).write_text(value)
        with pytest.raises(ValueError):m.compare_control(new,old)


@pytest.mark.parametrize('section', ['TileMap','TileSpecs','ArchSpecs'])
def test_changed_bitstream_semantics_rejected(control,section):
    new,old=control
    value=pickle.loads((new/'bitStreamSpec.bin').read_bytes())
    value[section]={}
    (new/'bitStreamSpec.bin').write_bytes(pickle.dumps(value))
    with pytest.raises(ValueError):m.compare_control(new,old)


def test_bad_pip_grammar_rejected():
    with pytest.raises(ValueError):m.graph_rows('a,b,c',pips=True)

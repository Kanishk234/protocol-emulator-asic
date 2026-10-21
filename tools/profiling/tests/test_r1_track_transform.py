from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from fold_tracks import fold_csv, transform


def test_directional_widths_change_without_touching_local_or_clock():
    text='NORTH,N1BEG,0,-1,N1END,8\nJUMP,JN2BEG,0,0,JN2END,8\nNORTH,N_GBUF_BEG,0,-1,N_GBUF_END,4\nEAST,NULL,1,0,E2END,8\n'
    assert fold_csv(text,4)==text.replace('N1END,8','N1END,4').replace('E2END,8','E2END,4')


def test_unexpected_original_width_rejected():
    with pytest.raises(ValueError):fold_csv('NORTH,N1BEG,0,-1,N1END,6\n',4)
    with pytest.raises(ValueError):fold_csv('',5)


def test_explicit_matrix_retains_merged_choices_and_empty_corner(tmp_path):
    from types import SimpleNamespace as NS
    directory=tmp_path/'tiles/tiny/example'
    directory.mkdir(parents=True)
    (directory/'example.csv').write_text('TILE,example\nMATRIX,old.list\nNORTH,N1BEG,0,-1,N1END,8\n')
    tiles=[NS(name='example',switch_matrix=NS(connections={
        'N1BEG0':['local0'], 'N1BEG4':['local4']})),
        NS(name='empty_corner',switch_matrix=NS(connections={}))]
    proposal=transform(tmp_path,tiles,4)
    assert (directory/'example_r1_folded.list').read_text()=='N1BEG0,local0\nN1BEG0,local4\n'
    assert 'MATRIX,./example_r1_folded.list' in (directory/'example.csv').read_text()
    assert proposal['example']['select_bits']==1
    assert 'empty_corner' not in proposal

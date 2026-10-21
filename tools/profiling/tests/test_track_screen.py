import copy
import pytest
from profiling.track_screen import fold_pin,screen


@pytest.mark.parametrize('tracks', [4,6,8])
def test_only_global_channel_names_fold(tracks):
    for prefix in ('N1BEG','E1END','S2BEGb','W2MID','N2END'):
        assert fold_pin(prefix+'7',tracks)==prefix+str(7%tracks)
    for name in ('JN2BEG7','JW2END7','J2MID_ABa_END3','N_GBUF_END3','GCLK_BEG0','CO0','LA_O'):
        assert fold_pin(name,tracks)==name


def test_folded_direct_edges_need_a_real_mux():
    connections={'N2BEG0':['JN2END0'],'N2BEG4':['JN2END4']}
    before=copy.deepcopy(connections)
    result=screen(connections,4)
    assert result['connections']=={'N2BEG0':['JN2END0','JN2END4']}
    assert result['select_bits']==1 and result['max_fanin']==2
    assert connections==before
    assert not result['physical_acceptance']


def test_duplicate_sources_collapse_and_oversized_mux_rejected_for_custom_flow():
    result=screen({'N1BEG0':['N1END0','N1END4']},4)
    assert result['select_bits']==0
    result=screen({'N1BEG0':['source'+str(i) for i in range(17)]},4)
    assert result['custom_mux_arity_supported'] is False


def test_bad_width_track_index_or_empty_mux_rejected():
    for tracks in (0,5,9):
        with pytest.raises(ValueError):fold_pin('N1END0',tracks)
    with pytest.raises(ValueError):fold_pin('N1END8',4)
    with pytest.raises(ValueError):screen({'N1BEG0':[]},4)
    with pytest.raises(ValueError):screen({},4)
    with pytest.raises(ValueError):screen({},5)

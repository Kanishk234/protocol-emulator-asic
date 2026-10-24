from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from detailed_leaf import check_inventories


def inventory():
    lines=[f'CELL\tc{i}\t'+('sg13cmos5l_dlhq_1' if i<334 else 'sg13cmos5l_buf_1')+'\t0\t0\t1\t1\tR0\tPLACED' for i in range(1453)]
    return '\n'.join(lines+['ITERM\tc0\tD\tnet','PORT\tIN\tnet\tINPUT\tSIGNAL',
                            'PBOX\tIN\tMetal2\t0\t0\t1\t1','PGTERMS\t2906'])+'\n'


def test_added_route_wires_preserve_frozen_cells_pins_and_connectivity():
    before=inventory()+'REQUIRED_NET\tnet\t0\n'
    after=inventory()+'REQUIRED_NET\tnet\t1\n'
    assert check_inventories(before,after)['required_signal_nets_with_wires']==1


@pytest.mark.parametrize('change',[lambda s:s.replace('PBOX\tIN\tMetal2','PBOX\tIN\tMetal3'),
                                  lambda s:s.replace('ITERM\tc0\tD\tnet','ITERM\tc0\tD\tother'),
                                  lambda s:s.replace('R0\tPLACED','MX\tPLACED',1)])
def test_router_cannot_change_pin_geometry_connectivity_or_placement(change):
    before=inventory();after=change(before)+'REQUIRED_NET\tnet\t1\n'
    with pytest.raises(ValueError,match='changed'):check_inventories(before,after)


def test_missing_or_duplicate_required_net_routes_fail():
    text=inventory()
    for rows in ['', 'REQUIRED_NET\tnet\t0\n', 'REQUIRED_NET\tnet\t1\n'*2]:
        with pytest.raises(ValueError):check_inventories(text,text+rows)


def test_unrouted_control_must_not_false_positive_and_net_population_must_match():
    text=inventory()
    with pytest.raises(ValueError,match='unrouted control'):
        check_inventories(text+'REQUIRED_NET\tnet\t1\n',text+'REQUIRED_NET\tnet\t1\n')
    with pytest.raises(ValueError,match='population'):
        check_inventories(text+'REQUIRED_NET\tnet\t0\n',text+'REQUIRED_NET\tother\t1\n')

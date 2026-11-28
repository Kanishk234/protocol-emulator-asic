from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from primitive_hold_probe import check_branch_identity,eco_script,FF,MASTER


def inventory(buffered=False):
    rows=[f'CELL\t_1_\t{FF}\t0\t0\t100\t100\tR0\tPLACED',
          'CELL\t_cfg_\tsg13cmos5l_dlhq_1\t100\t0\t200\t100\tR0\tPLACED',
          'ITERM\t_1_\tCLK\tclock','ITERM\t_1_\tQ\tq','ITERM\t_1_\tD\t'+('wp_r1_hold__1__net' if buffered else 'data'),
          'ITERM\t_cfg_\tD\tframe','ITERM\t_cfg_\tQ\tconfiguration',
          'PORT\tin\tdata\tINPUT\tSIGNAL','PBOX\tin\tMetal2\t0\t0\t10\t10']
    if buffered:
        rows += [f'CELL\twp_r1_hold__1_\t{MASTER}\t200\t0\t300\t100\tR0\tPLACED',
                 'ITERM\twp_r1_hold__1_\tA\tdata','ITERM\twp_r1_hold__1_\tX\twp_r1_hold__1__net',
                 'ITERM\twp_r1_hold__1_\tVDD\tVPWR','ITERM\twp_r1_hold__1_\tVSS\tVGND']
    return '\n'.join(rows)+'\n'


def test_only_buffer_identity_branch_and_original_geometry_are_admitted():
    r=check_branch_identity(inventory(),inventory(True),['_1_'])
    assert r['added_data_buffers']==1 and r['configuration_latches']==1
    assert r['binary_buffer_collapsed_connectivity_equal']


@pytest.mark.parametrize('old,new',[
    ('\tA\tdata','\tA\tq'),('VSS\tVGND','VSS\tVPWR'),
    ('_cfg_\tQ\tconfiguration','_cfg_\tQ\tq'),
    ('_1_\tCLK\tclock','_1_\tCLK\tdata'),
    ('PORT\tin\tdata','PORT\tin\tq'),
    ('\t0\t0\t100\t100','\t1\t0\t101\t100'),
    (MASTER,'sg13cmos5l_inv_1'),
])
def test_wrong_signal_power_config_pin_master_or_placement_fails(old,new):
    with pytest.raises(ValueError):check_branch_identity(inventory(),inventory(True).replace(old,new),['_1_'])


def test_incomplete_register_set_or_duplicate_terminal_fails():
    for targets in ([],['_1_','_1_']):
        with pytest.raises(ValueError):check_branch_identity(inventory(),inventory(True),targets)
    with pytest.raises(ValueError):
        check_branch_identity(inventory(),inventory(True)+'ITERM\t_1_\tCLK\tclock\n',['_1_'])


def test_script_locks_original_cells_and_changes_only_data_branch(tmp_path):
    script=eco_script(tmp_path/'source.odb',tmp_path,['_1_'],True)
    assert script.index('setPlacementStatus FIRM')<script.index('detailed_placement')
    assert 'check_placement -verbose' in script
    assert '$d disconnect;$d connect $branch' in script
    assert 'set_case_analysis' not in script and 'set_false_path' not in script
    with pytest.raises(ValueError):eco_script(tmp_path/'source.odb',tmp_path,['bad;command'],True)

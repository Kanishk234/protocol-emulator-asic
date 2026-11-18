"""Finishing must keep original logic and require every physical evidence gate."""
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from finish_leaf import GATES, check_finished_inventory, finishing_steps, gates_pass, identity


def inventory():
    return '\n'.join([f'CELL\tc{i}\tsg13cmos5l_buf_1\t0\t0\t1\t1\tR0\tPLACED' for i in range(1243)]+
                     ['PORT\tP\tn0\tINPUT\tSIGNAL', 'ITERM\tc0\tA\tn0']+
                     [f'REQUIRED_NET\tn{i}\t1' for i in range(1347)])+'\n'


def test_filler_can_be_added_without_changing_any_original_logic():
    source = inventory()
    final = source+'CELL\tf0\tsg13cmos5l_fill_1\t2\t0\t3\t1\tR0\tPLACED\n'
    assert check_finished_inventory(source, final)['added_fill_or_decap_cells'] == 1


@pytest.mark.parametrize('change', [
    lambda s: s+'CELL\tf0\tsg13cmos5l_buf_1\t2\t0\t3\t1\tR0\tPLACED\n',
    lambda s: s.replace('ITERM\tc0\tA\tn0', 'ITERM\tc0\tA\tother'),
    lambda s: s.replace('R0\tPLACED', 'MX\tPLACED', 1),
    lambda s: s.replace('REQUIRED_NET\tn0\t1', 'REQUIRED_NET\tn0\t0'),
    lambda s: s.replace('PORT\tP', 'PORT\tQ'),
])
def test_finishing_cannot_hide_logic_interface_or_wire_changes(change):
    source = inventory()
    with pytest.raises(ValueError):
        check_finished_inventory(source, change(source))


def test_every_physical_gate_is_required_and_zero():
    metrics = dict.fromkeys(GATES, 0)
    assert gates_pass(metrics)
    for key in GATES:
        for invalid in (None, 1, False, '0'):
            assert not gates_pass(dict(metrics, **{key: invalid}))
        missing = dict(metrics);del missing[key]
        assert not gates_pass(missing)


def test_unrelated_producer_is_rejected():
    with pytest.raises(ValueError, match='producer'):
        identity(dict(id=44394572610, conclusion='success'))


def test_repeated_antenna_stage_suffix_is_supported_but_absence_is_rejected():
    from types import SimpleNamespace
    ids = ['Odb.RemoveRoutingObstructions', 'OpenROAD.CheckAntennas-1',
           'Checker.TrDRC', 'Checker.DisconnectedPins', 'OpenROAD.FillInsertion',
           'OpenROAD.RCX', 'OpenROAD.STAPostPNR', 'KLayout.StreamOut', 'Magic.DRC',
           'KLayout.DRC', 'Checker.MagicDRC', 'Checker.KLayoutDRC',
           'Magic.SpiceExtraction', 'Netgen.LVS', 'Checker.LVS']
    stages = [SimpleNamespace(id=name) for name in ids]
    assert finishing_steps(stages) == stages
    with pytest.raises(ValueError, match='CheckAntennas'):
        finishing_steps([s for s in stages if s.id != 'OpenROAD.CheckAntennas-1'])

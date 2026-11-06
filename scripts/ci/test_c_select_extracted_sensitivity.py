import pytest

from c_select_extracted_sensitivity import CASES, TARGETS, change_netlist


def fixture():
    return '\n'.join(f'{old} {name} (.A(a), .Y(y));' for name, (old, new) in TARGETS.items())


@pytest.mark.parametrize('case', list(CASES))
def test_reviewed_cases_keep_connections(case):
    text=fixture()
    changed=change_netlist(text,CASES[case])
    assert changed.count('.A(a)')==len(TARGETS)
    assert changed.count('.Y(y)')==len(TARGETS)
    if case=='baseline': assert changed==text


@pytest.mark.parametrize('changes', [{'_27522_':'sg13cmos5l_nor4_4'},
                                    {'other':'sg13cmos5l_nor4_2'}])
def test_unreviewed_changes_refused(changes):
    with pytest.raises(AssertionError):change_netlist(fixture(),changes)


def test_wrong_original_cell_refused():
    with pytest.raises(AssertionError):
        change_netlist(fixture().replace('sg13cmos5l_nor4_1','sg13cmos5l_nand4_1'),CASES['nor4_first'])

import pytest
from electrical_load_inventory import inventory


def fixture(clock=False, mismatch=False):
    driver = 'clkbuf_test' if clock else 'driver'
    master = 'sg13cmos5l_buf_8' if clock else 'sg13cmos5l_buf_1'
    components = f'- {driver} {master} ;\n- ren_driver sg13cmos5l_nor2b_1 ;\n- ram RM_IHPSG13_1P_512x16_c2_bm_bist ;\n'
    components += ''.join(f'- sink{i} sg13cmos5l_buf_8 ;\n' for i in range(16))
    loads = ''.join(f'( sink{i} A ) ' for i in range(16))
    layout = f'COMPONENTS 19 ;\n{components}END COMPONENTS\nNETS 2 ;\n- data ( {driver} X ) {loads};\n- ren ( ren_driver Y ) ( ram A_REN ) ;\nEND NETS'
    report = f'{driver}/X 8 {15 if mismatch else 16} -8 (VIOLATED)\n'
    return layout, report


@pytest.mark.parametrize('clock', [False, True])
def test_complete_load_accounting_and_bounded_partition(clock):
    x = inventory(*fixture(clock))
    d = x['drivers'][0]
    assert d['loads'] == len(d['sinks']) == 16
    assert d['retained_loads'] + d['proposed_buffers'] <= d['group_load_budget']
    assert 16-d['retained_loads'] <= d['proposed_buffers']*d['group_load_budget']
    assert x['ren']['driver'] == ('ren_driver','Y')
    assert not x['physical_change_applied'] and not x['legal_sites_verified']


def test_report_def_disagreement_refused():
    with pytest.raises(ValueError, match='count mismatch'): inventory(*fixture(mismatch=True))


def test_clock_branch_with_data_load_refused():
    layout, report = fixture(clock=True)
    with pytest.raises(ValueError, match='clock topology'):
        inventory(layout.replace('( sink0 A )','( sink0 D )'), report)


def test_missing_ren_refused():
    layout, report = fixture()
    with pytest.raises(ValueError, match='SRAM REN'): inventory(layout.replace('A_REN','OTHER'), report)

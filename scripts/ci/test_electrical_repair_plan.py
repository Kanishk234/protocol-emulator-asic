import copy
import pytest
from electrical_repair_plan import validate_change, plan


def case():
    before='sg13cmos5l_buf_1 driver (.A(in), .X(net));\nsg13cmos5l_antennanp diode (.DIODE(net));\nsg13cmos5l_buf_1 sink (.A(net), .X(out));'
    after='sg13cmos5l_buf_1 driver (.A(in), .X(net));\nsg13cmos5l_antennanp diode (.DIODE(branch));\nsg13cmos5l_buf_1 sink (.A(branch), .X(out));\nsg13cmos5l_buf_4 added (.A(net), .X(branch));'
    proposal={'groups':[dict(buffer='added',net='branch',master='sg13cmos5l_buf_4',source_net='net',sinks=[('diode','DIODE'),('sink','A')])]}
    return before,after,proposal


def test_identity_repair_retains_diode_and_functional_connections():
    assert validate_change(*case())


@pytest.mark.parametrize('fault',['lost_diode','changed_driver','wrong_buffer','wrong_sink','duplicate_sink'])
def test_unplanned_mutations_refused(fault):
    before,after,p=case();p=copy.deepcopy(p)
    if fault=='lost_diode': after=after.replace('sg13cmos5l_antennanp diode (.DIODE(branch));','')
    elif fault=='changed_driver': after=after.replace('driver (.A(in)','driver (.A(other)')
    elif fault=='wrong_buffer': after=after.replace('sg13cmos5l_buf_4 added','sg13cmos5l_inv_1 added')
    elif fault=='wrong_sink': after=after.replace('sink (.A(branch)','sink (.A(net)')
    else: p['groups'][0]['sinks'].append(('sink','A'))
    with pytest.raises(ValueError): validate_change(before,after,p)


def test_unreviewed_physical_source_refused():
    with pytest.raises(ValueError,match='checkpoint'): plan('unreviewed','',None,None)


def bus_case():
    before='RM_IHPSG13_1P_512x16_c2_bm_bist ram (.A_ADDR({n8,n7,n6,n5,n4,n3,net,n1,n0}), .A_REN(ren)); sg13cmos5l_buf_1 driver (.A(in), .X(net));'
    after=before.replace('n3,net,n1','n3,branch,n1')+' sg13cmos5l_buf_4 added (.A(net), .X(branch));'
    p={'groups':[dict(buffer='added',net='branch',master='sg13cmos5l_buf_4',source_net='net',sinks=[('ram','A_ADDR[2]')])]}
    return before,after,p


def test_indexed_address_pin_matches_nine_bit_verilog_bus():
    assert validate_change(*bus_case())


@pytest.mark.parametrize('fault',['other_bit','wrong_target','width','non_bus'])
def test_sram_bus_audit_preserves_every_unplanned_bit(fault):
    before,after,p=bus_case()
    if fault=='other_bit': after=after.replace('n8,n7','changed,n7')
    elif fault=='wrong_target': after=after.replace('n3,branch,n1','branch,net,n1')
    elif fault=='width': after=after.replace('n8,n7,','n8,')
    else: after=after.replace('{n8,n7,n6,n5,n4,n3,branch,n1,n0}','address')
    with pytest.raises(ValueError): validate_change(before,after,p)


def resize_case():
    before='sg13cmos5l_nor4_1 _25245_ (.A(a), .B(b), .C(c), .D(d), .Y(y));'
    after=before.replace('nor4_1','nor4_2')
    p={'groups':[],'resizes':[dict(instance='_25245_',old_master='sg13cmos5l_nor4_1',new_master='sg13cmos5l_nor4_2',pins=dict(A='a',B='b',C='c',D='d',Y='y'))]}
    return before,after,p


def test_exact_nor4_strength_change_preserves_all_pins():
    assert validate_change(*resize_case())


@pytest.mark.parametrize('fault',['pin','function','identity'])
def test_strength_audit_rejects_unplanned_changes(fault):
    before,after,p=resize_case()
    if fault=='pin': after=after.replace('.A(a)','.A(other)')
    elif fault=='function': after=after.replace('nor4_2','nand4_2')
    else: p['resizes'][0]['new_master']='sg13cmos5l_nor4_4'
    with pytest.raises(ValueError): validate_change(before,after,p)

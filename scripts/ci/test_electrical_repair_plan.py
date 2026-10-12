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

import pytest
from slot_root_storage_audit import inspect_netlists


def netlist():
    gates=['sg13cmos5l_lgcp_1 \\u_chip.g_lane[%d].u_slots.g_word[%d].g_latch_storage.u_icg (.CLK(clk),.GATE(dec),.GCLK(gclk));'%(lane,word) for lane in range(2) for word in range(48)]
    return '\n'.join(gates)+'\n'+'\n'.join('sg13cmos5l_dfrbpq_1 ff%d_%d (.CLK(clk),.D(d),.Q(\\u_chip.g_lane[%d].kk[%d] ));'%(lane,bit,lane,bit) for lane in range(2) for bit in range(64))


def test_expected_reflex_gates_and_observed_constant_ff():
    r=inspect_netlists(netlist(),netlist())
    assert r['source_slot_clock_gates']==96
    assert r['removed_constant_bank_clock_gates']==8
    assert r['synthesis_constant_output_drivers'][0]['master']=='sg13cmos5l_dfrbpq_1'
    assert r['physical_qualification_performed'] is False


@pytest.mark.parametrize('fault',['old_constant_gate','missing_reflex_gate','wrong_master'])
def test_wrong_refinement_refuses(fault):
    text=netlist()
    if fault=='old_constant_gate':text+='sg13cmos5l_lgcp_1 \\u_chip.g_lane[0].u_slots.g_word[51].u_icg (.CLK(clk),.GATE(dec),.GCLK(c));'
    if fault=='missing_reflex_gate':text='\n'.join(text.splitlines()[1:])
    if fault=='wrong_master':text=text.replace('sg13cmos5l_lgcp_1','sg13cmos5l_buf_4',1)
    with pytest.raises(ValueError):inspect_netlists(text,netlist())


def test_gated_or_missing_constant_ff_refuses():
    text=netlist()
    with pytest.raises(ValueError,match='128root'):
        inspect_netlists(text.replace('ff0_0 (.CLK(clk)','ff0_0 (.CLK(gated_clk)'),text)
    with pytest.raises(ValueError,match='128root'):
        inspect_netlists(text.replace('sg13cmos5l_dfrbpq_1 ff0_0','sg13cmos5l_dlhq_1 ff0_0'),text)

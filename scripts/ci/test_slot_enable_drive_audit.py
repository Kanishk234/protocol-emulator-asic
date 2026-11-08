import pytest
from slot_enable_drive_audit import inspect_netlists


def netlist(variant):
    words=range(48,52) if variant=='constants' else range(52)
    return '\n'.join('sg13cmos5l_buf_4 \\u_chip.g_lane[%d].u_slots.g_word[%d].g_enable_drive.u_buf (.A(a), .X(x));'%(lane,word) for lane in range(2) for word in words)


@pytest.mark.parametrize('variant,count',[('constants',8),('all_words',104)])
def test_synthesis_actual_buffer_counts_and_native_retention(variant,count):
    text=netlist(variant);r=inspect_netlists(text,text,variant)
    assert r['source_buffer_count']==count and r['final_retained_buffer_count']==count
    assert r['synthesis_source_buffers_preserved'] is True
    assert r['physical_qualification_performed'] is False


def test_native_buffer_removal_is_reported_without_false_preservation_claim():
    text=netlist('constants');final='\n'.join(text.splitlines()[1:])
    r=inspect_netlists(text,final,'constants')
    assert r['final_retained_buffer_count']==7 and len(r['removed_by_native_optimization'])==1


@pytest.mark.parametrize('fault',['missing','wrongmaster','wrongscope'])
def test_synthesis_must_exercise_reviewed_source_cells(fault):
    text=netlist('constants');final=text
    if fault=='missing':text='\n'.join(text.splitlines()[1:])
    if fault=='wrongmaster':text=text.replace('sg13cmos5l_buf_4','sg13cmos5l_buf_2',1)
    if fault=='wrongscope':text=text.replace('g_word[48]','g_word[47]')
    with pytest.raises(ValueError,match='retain'):inspect_netlists(text,final,'constants')

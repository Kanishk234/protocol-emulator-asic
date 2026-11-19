from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from assembly_ports import annotate_script,context_masters,context_port_block,flat_spice_script,retain_original_script,spice_ports,strict_verdict


def test_spice_ports_include_continuations_and_reject_empty_top_interface():
    text='* generated\n.subckt top a b\n+ c d\n.ends\n'
    assert spice_ports(text,'top')==list('abcd')
    assert spice_ports('.subckt top\n.ends\n','top')==[]
    with pytest.raises(ValueError):strict_verdict('Final result: Circuits match uniquely.\n',[],list('abcd'))


@pytest.mark.parametrize('report',[
    'Final result: Top level cell failed pin matching.\n',
    'Netlists match uniquely.\n',
    'Final result: Circuits match uniquely with port errors.\n',
    'Final result: Circuits match uniquely.\nFinal result: Circuits match uniquely.\n'])
def test_zero_summary_counts_cannot_override_failed_or_missing_final_verdict(report):
    with pytest.raises(ValueError):strict_verdict(report,list('ab'),list('ab'))


def test_unique_match_requires_complete_distinct_declared_ports():
    report='Final result: Circuits match uniquely.\n'
    assert strict_verdict(report,list('ab'),list('ab'))
    for actual in [['a'],['a','b','c'],['a','a']]:
        with pytest.raises(ValueError):strict_verdict(report,actual,list('ab'))
    with pytest.raises(ValueError):spice_ports('.subckt top a a\n.ends','top')


def test_annotation_only_promotes_root_interface_and_keeps_extraction_commands():
    pins=['VPWR','VGND']+[f'p{i}' for i in range(447)]
    source='load $::env(DESIGN_NAME) -dereference\nextract unique $::env(MAGIC_EXT_UNIQUE)\nextract\n'
    patched=annotate_script(source,pins)
    assert patched.count('port makeall')==1
    assert 'R1_EXPORTED_PORTS' in patched
    assert patched.endswith('extract unique $::env(MAGIC_EXT_UNIQUE)\nextract\n')
    assert 'flatten' not in patched and 'erase' not in patched and 'paint' not in patched
    with pytest.raises(ValueError):annotate_script(source,pins[:-1])
    with pytest.raises(ValueError):annotate_script(source+source,pins)
    with pytest.raises(ValueError):annotate_script(source,pins[:-1]+['p];error danger'])


def test_foreign_runtime_script_is_retained_but_never_patched_or_executed(tmp_path):
    source=tmp_path/'foreign.tcl';source.write_text('error foreign\n')
    with pytest.raises(ValueError,match='retained for review'):
        retain_original_script(source,tmp_path)
    assert (tmp_path/'original-extract-spice.tcl').read_bytes()==source.read_bytes()
    assert not (tmp_path/'extract_ports.tcl').exists()


def test_only_complete_context_wrappers_can_be_flattened_for_lvs():
    catalog=dict(contexts={str(i):dict(planned_master='wp_r1_context_'+str(i)) for i in range(26)})
    assert len(context_masters(catalog))==26
    for bad in ['sg13cmos5l_dlhq_1','*','wp_r1_context_0']:
        catalog['contexts']['25']['planned_master']=bad
        with pytest.raises(ValueError):context_masters(catalog)


def test_context_annotation_is_complete_and_keeps_each_native_interface_separate():
    contexts={'wp_r1_context_'+str(i):dict(pins=['FrameData[0]','VPWR','VGND'],width_dbu=10000,height_dbu=10000) for i in range(26)}
    text=context_port_block(contexts)
    assert text.count('port makeall')==26 and text.count('R1_CONTEXT_PORTS')==26
    assert 'flatten' not in text and 'paint' not in text and 'erase' not in text
    contexts['wp_r1_context_0']['pins'].append('bad];error injected')
    with pytest.raises(ValueError):context_port_block(contexts)
    with pytest.raises(ValueError):context_port_block({})


def test_flat_spice_export_changes_only_representation_after_unchanged_extraction():
    source='extract\next2spice lvs\next2spice short resistor\next2spice -o $netlist $::env(DESIGN_NAME).ext\n'
    changed=flat_spice_script(source)
    assert changed.replace('ext2spice hierarchy off\n','')==source
    for invalid in [source+source,'extract\n',changed]:
        with pytest.raises(ValueError):flat_spice_script(invalid)

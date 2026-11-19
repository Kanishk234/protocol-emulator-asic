from pathlib import Path
import json
import struct
import sys
import zipfile

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from assemble import UNITS, check_database, rename_lef, rename_netlist, top_netlist
from assembly_fetch import admit_run, extract
from gds_contexts import (fingerprint,labels,library,merge_contexts,record,records,
                          string,text,top_structure,translated_label)


def fake_library(master,shared_geometry=b'AB',timestamp=0):
    dates=record(5,2,bytes([timestamp])*24)
    shared=dates+string(6,'shared')+record(8)+record(16,3,shared_geometry)+record(17)+record(7)
    leaf=dates+string(6,master)+record(10)+string(18,'shared')+record(16,3,struct.pack('>ii',0,0))+record(17)+record(7)
    return record(0,2,b'\x02X')+record(1,2,bytes(24))+string(2,'library')+UNITS+shared+leaf+record(4)


def test_context_rename_preserves_all_geometry_and_reuses_only_identical_shared_cells():
    a=fake_library('leaf',timestamp=0);b=fake_library('leaf',timestamp=1)
    h,c,shared=merge_contexts([('a','leaf','context_a',a),('b','leaf','context_b',b)])
    assert set(c)=={'shared','context_a','context_b'} and set(shared)=={'shared'}
    assert fingerprint(library(a)[2]['shared'])==fingerprint(library(b)[2]['shared'])
    for name in ['context_a','context_b']:
        rs=list(records(c[name]))
        assert [text(r) for k,d,r in rs if k==6]==[name]
        assert [text(r) for k,d,r in rs if k==18]==['shared']
    assembled=h+b''.join(c.values())+top_structure('top',[
        dict(planned_master='context_a',origin_dbu=[0,0]),
        dict(planned_master='context_b',origin_dbu=[100,0])],200,100,[])+record(4)
    _,_,cells=library(assembled)
    assert len(cells)==4
    xy=[r[4:] for k,d,r in records(cells['top']) if k==16]
    assert xy[:2]==[struct.pack('>ii',0,0),struct.pack('>ii',100,0)]


def test_different_shared_geometry_is_never_silently_overwritten():
    with pytest.raises(ValueError,match='different geometry'):
        merge_contexts([('a','leaf','a',fake_library('leaf')),
                        ('b','leaf','b',fake_library('leaf',shared_geometry=b'CD'))])


@pytest.mark.parametrize('fault',['length','truncated','duplicate','units','reference','trailing'])
def test_malformed_or_inconsistent_gds_cannot_be_merged(fault):
    a=fake_library('leaf'); b=fake_library('leaf')
    if fault=='length':b=b'\x00\x03'+b[2:]
    if fault=='truncated':b=b[:-3]
    if fault=='duplicate':b=b.replace(string(6,'leaf'),string(6,'shared'))
    if fault=='units':b=b.replace(UNITS,UNITS[:-1]+bytes([UNITS[-1]^1]))
    if fault=='reference':b=b.replace(string(18,'shared'),string(18,'absent'))
    if fault=='trailing':b+=record(4)
    with pytest.raises(ValueError):
        merge_contexts([('a','leaf','a',a),('b','leaf','b',b)])


def test_exported_label_preserves_layer_type_and_translates_actual_position():
    e=[record(12),record(13,2,struct.pack('>h',30)),record(22,2,struct.pack('>h',25)),
       record(16,3,struct.pack('>ii',10,20)),string(25,'leaf_pin'),record(17)]
    copied=translated_label(e,'external[0]',[100,200])
    label=list(labels(copied))[0]
    assert label[0]=='external[0]'
    assert next(r[4:] for k,d,r in records(copied) if k==16)==struct.pack('>ii',110,220)
    assert [r for k,d,r in records(copied) if k in (13,22)]==e[1:3]


def test_lef_foreign_and_end_and_netlist_declaration_all_rename():
    source='MACRO leaf\n  FOREIGN leaf ;\n  SIZE 1 BY 1 ;\nEND leaf\nEND LIBRARY\n'
    result=rename_lef(source,'leaf','context')
    assert 'MACRO context\n' in result and 'FOREIGN context ;' in result and 'END context\n' in result
    assert rename_netlist('module leaf (a);\nendmodule\n','leaf','context').startswith('module context (')
    with pytest.raises(ValueError):rename_lef(source.replace('FOREIGN','WRONG'),'leaf','context')
    with pytest.raises(ValueError):rename_netlist('module wrong (a);','leaf','context')


def test_top_netlist_keeps_actual_bus_order_hierarchy_and_supplies():
    top=dict(ports=dict(data=dict(direction='input',bits=[2,3]),
                        answer=dict(direction='output',bits=[4])),
             cells=dict(tile=dict(connections=dict(in_bus=[2,3],out_pin=[4]))))
    source=top_netlist(top,[dict(instance='tile',planned_master='context')])
    assert 'input [1:0] data;' in source and 'assign n_2 = data[0];' in source
    assert 'assign answer = n_4;' in source and '.in_bus({n_3, n_2})' in source
    assert '.VPWR(VPWR)' in source and '.VGND(VGND)' in source
    assert 'context tile (' in source and "1'b" not in source


def test_archive_traversal_and_duplicate_names_are_rejected(tmp_path):
    for name in ['../outside','/absolute','folder/../outside','folder\\outside']:
        path=tmp_path/'bad.zip'
        with zipfile.ZipFile(path,'w') as bundle:bundle.writestr(name,'x')
        with pytest.raises(ValueError):extract(path,tmp_path/'output')


def test_foreign_run_attempt_cannot_replace_a_qualified_source():
    expected=dict(id=1,run_attempt=1,head_sha='a'*40,conclusion='failure')
    admit_run(dict(expected,status='completed'),expected)
    for key,value in [('run_attempt',2),('conclusion','success'),('head_sha','b'*40)]:
        with pytest.raises(ValueError):admit_run(dict(expected,**{key:value},status='completed'),expected)


@pytest.mark.parametrize('fault',[None,'master','position','box','signal','supply'])
def test_physical_database_must_preserve_masters_positions_pins_and_connectivity(tmp_path,fault):
    cat=dict(instances=[dict(instance='tile',planned_master='context',context='a',origin_dbu=[0,0])],
             contexts=dict(a=dict(width_dbu=100,height_dbu=100)))
    pins={n:dict(direction=d,kind=k,access=[dict(boxes=[['Metal3',[0,0,10,10]]])])
          for n,d,k in [('p','INPUT','SIGNAL'),('VPWR','INOUT','POWER'),('VGND','INOUT','GROUND')]}
    top=dict(ports=dict(p=dict(bits=[2])),cells=dict(tile=dict(connections=dict(i=[2]))))
    for file,data in [('catalog',cat),('pins',pins),('top',top)]:
        (tmp_path/(file+'.json')).write_text(json.dumps(data))
    data='CELL\ttile\tcontext\t0\t0\t100\t100\tR0\tFIRM\n'
    data+='ITERM\ttile\ti\tdata\nITERM\ttile\tVPWR\tVPWR\nITERM\ttile\tVGND\tVGND\n'
    for n,d,k in [('p','INPUT','SIGNAL'),('VPWR','INOUT','POWER'),('VGND','INOUT','GROUND')]:
        data+=f'PORT\t{n}\t'+('data' if n=='p' else n)+f'\t{d}\t{k}\n'
        data+=f'PBOX\t{n}\tMetal3\t0\t0\t10\t10\n'
    if fault=='master':data=data.replace('\tcontext\t','\twrong\t')
    if fault=='position':data=data.replace('\t100\t100\tR0','\t101\t100\tR0')
    if fault=='box':data=data.replace('PBOX\tp\tMetal3\t0','PBOX\tp\tMetal3\t1')
    if fault=='signal':data=data.replace('ITERM\ttile\ti\tdata','ITERM\ttile\ti\tother')
    if fault=='supply':data=data.replace('ITERM\ttile\tVPWR\tVPWR','ITERM\ttile\tVPWR\tVGND')
    (tmp_path/'assembled.txt').write_text(data)
    if fault is None:
        assert check_database(tmp_path)['signal_instance_terminals']==1
    else:
        with pytest.raises(ValueError):check_database(tmp_path)

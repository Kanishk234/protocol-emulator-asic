"""Exact extracted-source endpoint delay proposal; no physical qualification."""
import hashlib
from pathlib import Path
import re
from electrical_load_inventory import def_identifier
from event_nor2_screen import logical_cells
from fanout_sram_plan import occupancy
from incremental_repair_audit import placements
from sram_bank_plan import allocate

NL_SHA='6057d7fba86a86d1debf1c9e0fd3ded7e87714c3a234ec0afa8205e3e11f42c8'
DEF_SHA='ad54425d496dcc532e919bad25836c9b0b6a4de9fe0d0c2531cd1a9b1c53bca0'
REPORT_SHA='94577900dc2cc7b6b073e96ad8ab17785048f4af45ebf54507629fadb885a899'
MASTER='sg13cmos5l_dlygate4sd1_1'


def endpoints(report):
    if 'nom_fast_1p32V_m40C' not in report:raise ValueError('Wrong hold corner')
    result={}
    blocks=report.split('Startpoint:')[1:]
    if not blocks:raise ValueError('Missing hold paths')
    for block in blocks:
        slack=re.findall(r'([-\d.]+)\s+slack \((?:MET|VIOLATED)\)',block)
        endpoint=re.search(r'^Endpoint: (\S+) \(rising edge-triggered flip-flop',block,re.M)
        if len(slack)!=1:raise ValueError('Incomplete or ambiguous hold path')
        value=float(slack[0])
        if value<.05:
            if not endpoint:raise ValueError('Unreviewed hold endpoint type')
            name=endpoint[1];result[name]=min(value,result.get(name,value))
    if not result:raise ValueError('No sub-50ps endpoints')
    return result


def plan(netlist,layout,report,std_lef):
    for text,digest in ((netlist,NL_SHA),(layout,DEF_SHA),(report,REPORT_SHA)):
        if hashlib.sha256(text.encode()).hexdigest()!=digest:raise ValueError('Wrong extracted hold source')
    failing=endpoints(report)
    if len(failing)!=19:raise ValueError('Wrong reviewed endpoint set')
    cells=logical_cells(netlist);location=placements(layout)
    sections=layout.split('\nNETS ',1)[1].split('END NETS',1)[0];nets={};attached={}
    for entry in sections.split(';'):
        match=re.search(r'^\s*- (\S+)',entry)
        if not match:continue
        name=def_identifier(match[1]);terms=re.findall(r'\(\s*(\S+)\s+(\S+)\s*\)',entry.split(' + ',1)[0])
        nets[name]=terms
        for inst,pin in terms:
            if (inst,pin) in attached:raise ValueError('Multiple nets on one pin')
            attached[(inst,pin)]=name
    size,boxes=occupancy(layout,std_lef,1000,'__none__',MASTER)
    rows=[]
    for x,y,orient,count,pitch in re.findall(r'^ROW \S+ CoreSite (\d+) (\d+) (N|FS) DO (\d+) BY 1 STEP (\d+) 0 ;',layout,re.M):
        x,y,count,pitch=map(int,(x,y,count,pitch))
        if y<241920:
            shift=max(0,(260000-x+pitch-1)//pitch);x+=shift*pitch;count-=shift
        if count>0:rows.append((x,y,orient,count,pitch))
    groups=[]
    for sink,slack in sorted(failing.items(),key=lambda item:item[1]):
        master,pins=cells[sink];pins=dict(pins)
        if master!='sg13cmos5l_dfrbpq_1' or set(pins)!={'D','CLK','Q','RESET_B'}:
            raise ValueError('Unreviewed hold flop')
        source=attached[(sink,'D')]
        if pins['D'].strip().removeprefix('\\')!=source:raise ValueError('Hold NL/DEF disagreement')
        drivers=[(n,p) for n,p in nets[source] if p in ('X','Y','Q')]
        if len(drivers)!=1:raise ValueError('Missing unique hold data driver')
        name='tripwire_extracted_hold_'+sink.strip('_');net=name+'_net'
        if name in location or net in nets:raise ValueError('Repeated extracted hold repair')
        distance,x,y,orient=allocate(rows,boxes,name,*size,location[sink][1:3])
        boxes.append((name,x,y,x+size[0],y+size[1]))
        groups.append(dict(buffer=name,net=net,source_net=source,rail_source=sink,master=MASTER,
            sinks=[(sink,'D')],location=[x,y,orient],target_distance_dbu=distance,
            original_fast_hold_ns=slack,kind='endpoint-hold'))
    return dict(source_run=38305592967,netlist_sha256=NL_SHA,def_sha256=DEF_SHA,report_sha256=REPORT_SHA,
        groups=groups,added_buffers=len(groups),added_footprint_um2=len(groups)*size[0]*size[1]/1e6,
        minimum_fast_hold_ns=.05,footprint_overlap_count=0,detailed_legalization_required=True,
        physical_change_applied=False,physical_timing_measured=False,official_signoff=False)

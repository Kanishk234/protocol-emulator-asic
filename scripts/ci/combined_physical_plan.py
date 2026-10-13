"""Source-bound setup/hold/electrical proposal from actual extracted failures."""
import hashlib
import json
import re
from electrical_load_inventory import def_identifier
from electrical_report import audit
from event_nor2_screen import logical_cells
from extracted_hold_targets import endpoints,NL_SHA,DEF_SHA,REPORT_SHA
from extracted_setup_finish import CASES,TARGETS
from fanout_sram_plan import occupancy
from incremental_repair_audit import placements
from sram_bank_plan import allocate,MACRO_LEF_SHA

SETUP=CASES['and4']
CHECKS_SHA={'nom_typ_1p20V_25C': '2b40b3517d3df5320d95111b8cbe1ec7aca5c7076e883a7c6c870d24d49f0316', 'nom_slow_1p08V_125C': 'fd3aae8966dc17a3582658d73d5d4c8d39b1d76f1a4cc8e61305e8e75c816c3c', 'nom_fast_1p32V_m40C': 'f371399a350c139de01ff95f7d8cda67dca2e225053c00687a819e688e19f8ec'}



def source_binding():
    return dict(source_run=38305592967,nl_sha=NL_SHA,def_sha=DEF_SHA,report_sha=REPORT_SHA,
        checks_sha=CHECKS_SHA,setup=SETUP,targets=TARGETS,prefix='tripwire_combined_',hold_count=19,electrical_nets=29)

def connections(layout):
    nets={};attached={}
    for entry in layout.split('\nNETS ',1)[1].split('END NETS',1)[0].split(';'):
        hit=re.search(r'^\s*- (\S+)',entry)
        if not hit:continue
        name=def_identifier(hit[1])
        terms=[(n,def_identifier(p)) for n,p in re.findall(r'\(\s*(\S+)\s+(\S+)\s*\)',entry.split(' + ',1)[0])]
        if name in nets:raise ValueError('Duplicate source net')
        nets[name]=terms
        for pin in terms:
            if pin in attached:raise ValueError('Duplicate attached pin')
            attached[pin]=name
    return nets,attached



def standard_anchor(terms,locations):
    anchors=[n for n,p in terms if n!='u_chip.u_sram.sram' and locations[n][0].startswith('sg13cmos5l_')]
    if not anchors:raise ValueError('Missing standard-cell power anchor')
    return anchors[0]

def source_rows(layout):
    rows=[]
    for x,y,o,count,pitch in re.findall(r'^ROW \S+ CoreSite (\d+) (\d+) (N|FS) DO (\d+) BY 1 STEP (\d+) 0 ;',layout,re.M):
        x,y,count,pitch=map(int,(x,y,count,pitch))
        if y<241920:
            shift=max(0,(260000-x+pitch-1)//pitch);x+=shift*pitch;count-=shift
        if count>0:rows.append((x,y,o,count,pitch))
    if not rows:raise ValueError('No source rows')
    return rows


def macro_pin(layout,macro_lef,pin):
    # Exact known macro placement is FS at12um,40um; LEF height191.34um.
    if not re.search(r'- u_chip.u_sram.sram RM_IHPSG13_1P_512x16_c2_bm_bist\s+\+ FIXED \( 12000 40000 \) FS',layout):
        raise ValueError('Wrong macro placement')
    hit=re.search(r'PIN '+re.escape(pin)+r'\s(.*?)END '+re.escape(pin),macro_lef.read_text(),re.S)
    rects=re.findall(r'RECT\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)',hit[1]) if hit else []
    if not rects:raise ValueError('Missing macro pin geometry')
    x1,y1,x2,y2=map(float,rects[0])
    return [round((12+(x1+x2)/2)*1000),round((40+191.34-(y1+y2)/2)*1000)]


def plan(netlist,layout,hold_report,checks,std_lef,macro_lef,binding=None):
    cfg=source_binding() if binding is None else binding
    setup,targets=cfg['setup'],cfg['targets']
    for text,digest in ((netlist,cfg['nl_sha']),(layout,cfg['def_sha']),(hold_report,cfg['report_sha'])):
        if hashlib.sha256(text.encode()).hexdigest()!=digest:raise ValueError('Wrong combined source')
    if hashlib.sha256(macro_lef.read_bytes()).hexdigest()!=MACRO_LEF_SHA:raise ValueError('Wrong macro LEF')
    loc=placements(layout);nets,attached=connections(layout);rows=source_rows(layout)
    cells={n.strip().removeprefix('\\'):(m,p) for n,(m,p) in logical_cells(netlist).items()}
    sizes={};boxes=None
    for master in set(setup.values())|{'sg13cmos5l_buf_4','sg13cmos5l_dlygate4sd1_1'}:
        size,occupied=occupancy(layout,std_lef,1000,'__none__',master);sizes[master]=size
        if boxes is None:boxes=occupied
    resizes=[]
    for name,new in setup.items():
        old=targets[name][0]
        if cells[name][0]!=old or loc[name][0]!=old:raise ValueError('Wrong setup master')
        pins={p:v.strip().removeprefix('\\') for p,v in cells[name][1]}
        width,height=sizes[new];distance,x,y,o=allocate(rows,boxes,name,width,height,loc[name][1:3])
        boxes=[b for b in boxes if b[0]!=name]+[(name,x,y,x+width,y+height)]
        old_size,_=occupancy(layout,std_lef,1000,name,old)
        resizes.append(dict(instance=name,old_master=old,new_master=new,pins=pins,
            location=[x,y,o],origin_displacement_dbu=distance,area_delta_um2=(width*height-old_size[0]*old_size[1])/1e6))
    failing=endpoints(hold_report,cfg.get('hold_target_ns',.05))
    if len(failing)!=cfg['hold_count']:raise ValueError('Wrong hold endpoint set')
    groups=[];moved=set()
    def add(source,sinks,master,target,kind):
        if not sinks or any(pin in moved for pin in sinks):raise ValueError('Duplicate/empty sink group')
        if any(pin in ('CLK','GCLK','GATE','RESET_B') for n,pin in sinks):raise ValueError('Clock/reset rewire refused')
        if any(attached.get(pin)!=source for pin in sinks):raise ValueError('Wrong source sink')
        index=len(groups);name=cfg['prefix']+str(index);new_net=name+'_net'
        if name in loc or new_net in nets:raise ValueError('Repeated combined repair')
        width,height=sizes[master];distance,x,y,o=allocate(rows,boxes,name,width,height,target)
        boxes.append((name,x,y,x+width,y+height));moved.update(sinks)
        # Macro rails are VDD!/VSS!, whereas the identity-cell helper needs
        # ordinary standard-cell VDD/VSS terminals. Never use a macro anchor.
        anchor=standard_anchor(nets[source],loc)
        groups.append(dict(buffer=name,net=new_net,source_net=source,rail_source=anchor,
            master=master,sinks=sinks,location=[x,y,o],kind=kind,target_distance_dbu=distance))
    for sink in sorted(failing,key=failing.get):
        if cells[sink][0]!='sg13cmos5l_dfrbpq_1':raise ValueError('Unreviewed hold flop')
        add(attached[(sink,'D')],[(sink,'D')],'sg13cmos5l_dlygate4sd1_1',loc[sink][1:3],'hold')
    failures={}
    for corner,text in checks.items():
        if corner not in text or corner not in cfg['checks_sha'] or hashlib.sha256(text.encode()).hexdigest()!=cfg['checks_sha'][corner]:raise ValueError('Wrong electrical report corner/source')
        for kind,violations in audit(text)['violations'].items():
            for row in violations:
                name,pin=row.split()[0].rsplit('/',1);source=attached[(name,pin)]
                failures.setdefault(source,set()).add(kind)
    if len(checks)!=3 or len(failures)!=cfg['electrical_nets']:raise ValueError('Wrong measured electrical target set')
    for source,kinds in sorted(failures.items()):
        terms=nets[source]
        drivers=[p for p in terms if p[1] in ('X','Y','Q') or p[1].startswith('A_DOUT[')]
        if len(drivers)!=1:raise ValueError('Missing unique data driver')
        driver=drivers[0]
        remaining=[p for p in terms if p!=driver and p not in moved]
        # Old hold sinks on this source already become one delay-input load.
        # Leave one slot for each existing new hold input; all other consumers
        # move behind max4-load buffers, including existing antenna diodes.
        hold_inputs=sum(g['source_net']==source for g in groups)
        if hold_inputs+(len(remaining)+3)//4>8:raise ValueError('Source driver would remain over fanout budget')
        def point(pin):
            n,p=pin
            return macro_pin(layout,macro_lef,p) if n=='u_chip.u_sram.sram' else list(loc[n][1:3])
        remaining.sort(key=lambda pin:(point(pin)[0],point(pin)[1],pin))
        for start in range(0,len(remaining),4):
            selected=remaining[start:start+4]
            if driver[0]=='u_chip.u_sram.sram':target=point(driver)
            elif any(n=='u_chip.u_sram.sram' for n,p in selected):target=point(next(p for p in selected if p[0]=='u_chip.u_sram.sram'))
            elif 'slew' in kinds:target=list(loc[driver[0]][1:3])
            else:target=[sum(point(p)[i] for p in selected)//len(selected) for i in (0,1)]
            add(source,selected,'sg13cmos5l_buf_4',target,'electrical')
    for group in groups:
        x,y,o=group['location'];w,h=sizes[group['master']]
        if any(n!=group['buffer'] and l<x+w and rr>x and b<y+h and t>y for n,l,b,rr,t in boxes):raise ValueError('Combined footprint overlap')
    return dict(source_run=cfg['source_run'],def_sha256=cfg['def_sha'],netlist_sha256=cfg['nl_sha'],
        groups=groups,resizes=resizes,added_buffers=len(groups),hold_delay_cells=cfg['hold_count'],
        electrical_target_nets=cfg['electrical_nets'],added_footprint_um2=sum(sizes[g['master']][0]*sizes[g['master']][1]/1e6 for g in groups),
        resize_area_delta_um2=sum(r['area_delta_um2'] for r in resizes),footprint_overlap_count=0,
        detailed_legalization_required=True,physical_change_applied=False,physical_timing_measured=False,official_signoff=False)


def setup_netlist(text,proposal,binding=None):
    cfg=source_binding() if binding is None else binding
    expected=dict(cfg['setup']);resizes=proposal['resizes']
    if {r['instance']:r['new_master'] for r in resizes}!=expected or len(resizes)!=len(expected):raise ValueError('Wrong combined setup set')
    old=logical_cells(text);wanted=dict(old);result=text
    for r in resizes:
        n=r['instance'];master,pins=old[n]
        if master!=cfg['targets'][n][0] or r['old_master']!=master or {p:v.strip().removeprefix('\\') for p,v in pins}!=r['pins']:raise ValueError('Wrong resize identity')
        pattern=r'\b'+re.escape(master)+r'(\s+)'+re.escape(n)+r'(?=\s*\()'
        result,count=re.subn(pattern,lambda m:r['new_master']+m[1]+n,result)
        if count!=1:raise ValueError('Ambiguous resize')
        wanted[n]=(r['new_master'],pins)
    if logical_cells(result)!=wanted:raise ValueError('Resize changed connections')
    return result


def validate_change(before,after,proposal,binding=None):
    from electrical_repair_plan import validate_change as buffers
    buffers(setup_netlist(before,proposal,binding),after,{'groups':proposal['groups']})


def target_call(layout,proposal,binding=None):
    cfg=source_binding() if binding is None else binding
    if hashlib.sha256(layout.encode()).hexdigest()!=cfg['def_sha'] or proposal['source_run']!=cfg['source_run'] or proposal['def_sha256']!=cfg['def_sha']:
        raise ValueError('Wrong combined Tcl source')
    nets,_=connections(layout);masters={n:p[0] for n,p in placements(layout).items()}
    def word(value):
        if not re.fullmatch(r'[A-Za-z0-9_./\[\]\-]+',value):raise ValueError('Unsafe combined Tcl identity')
        return '{'+value+'}'
    serialized=[]
    for r in proposal['resizes']:
        name=r['instance']
        if name not in cfg['setup'] or r['new_master']!=cfg['setup'][name] or r['old_master']!=cfg['targets'][name][0]:raise ValueError('Unreviewed combined resize')
        pins=' '.join(word(p)+' '+word(n) for p,n in sorted(r['pins'].items()))
        serialized.append('{'+word(name)+' '+word(r['old_master'])+' '+word(r['new_master'])+' {'+pins+'}}')
        masters[name]=r['new_master']
    lines=['tripwire_size_electrical {'+' '.join(serialized)+'}']
    for r in proposal['resizes']:
        x,y,o=r['location'];lines.append('tripwire_place_combined '+word(r['instance'])+' '+word(r['new_master'])+' {'+f'{x} {y} {o}'+'}')
    lines.append('set tripwire_frozen [tripwire_freeze_existing_placement]')
    for net in dict.fromkeys(g['source_net'] for g in proposal['groups']):
        groups=[g for g in proposal['groups'] if g['source_net']==net]
        master=groups[0]['master']
        if any(g['master']!=master for g in groups):raise ValueError('Mixed repair masters on source')
        if master not in ('sg13cmos5l_buf_4','sg13cmos5l_dlygate4sd1_1'):raise ValueError('Unreviewed combined buffer master')
        terms=nets[net];pins=' '.join(word(n+'/'+p) for n,p in terms)
        types=' '.join('{'+word(n)+' '+word(masters[n])+'}' for n in sorted({n for n,p in terms}))
        expectations='{'+word(net)+' {'+pins+'} {'+types+'}}'
        mutations=[]
        for g in groups:
            identity=' '.join(word(g[k]) for k in ('buffer','net','source_net','rail_source'))
            position=' '.join(map(str,g['location']));sinks=' '.join('{'+word(n)+' '+word(p)+'}' for n,p in g['sinks'])
            mutations.append('{'+identity+' {'+position+'} {'+sinks+'}}')
        lines.append('tripwire_electrical_repair '+word(master)+' {'+expectations+'} {'+' '.join(mutations)+'}')
    return '\n'.join(lines)+'\n'

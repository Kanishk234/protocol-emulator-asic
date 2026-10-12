"""Exact final-checkpoint identity-buffer plan; physical qualification required."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from electrical_load_inventory import inventory
from fanout_sram_plan import occupancy
from sram_bank_plan import allocate, MACRO_LEF_SHA

DEF_SHA = 'e8512f53f6f4d4c16bab1724b48f91ed9fad34ee105a11d0579ac3a8bef0e11b'


def plan(layout, checks, std_lef, macro_lef):
    if hashlib.sha256(layout.encode()).hexdigest() != DEF_SHA:
        raise ValueError('Wrong final electrical checkpoint')
    if hashlib.sha256(macro_lef.read_bytes()).hexdigest() != MACRO_LEF_SHA:
        raise ValueError('Wrong macro pin geometry')
    if not re.search(r'UNITS DISTANCE MICRONS 1000\b', layout):
        raise ValueError('Wrong DEF units')
    if not re.search(r'- u_chip.u_sram.sram RM_IHPSG13_1P_512x16_c2_bm_bist\s+\+ FIXED \( 12000 40000 \) FS', layout):
        raise ValueError('Wrong SRAM placement')
    audit = inventory(layout, checks)
    sizes = {}
    boxes = None
    for master in ('sg13cmos5l_buf_4','sg13cmos5l_buf_8'):
        size, occupied = occupancy(layout, std_lef, 1000, '__none__', master)
        sizes[master] = size
        if boxes is None: boxes = occupied
    rows = [(int(x),int(y),o,int(n),int(p)) for x,y,o,n,p in re.findall(
        r'^ROW \S+ CoreSite (\d+) (\d+) (N|FS) DO (\d+) BY 1 STEP (\d+) 0 ;', layout,re.M)
        if int(y)>=241920]
    if not rows: raise ValueError('Missing legal rows above macro halo')
    positions = {name:(left,bottom) for name,left,bottom,right,top in boxes}
    groups = []
    for driver in audit['drivers']:
        origin = positions[driver['instance']]
        ordered = sorted(driver['sinks'],key=lambda s:(sum(abs(positions[s[0]][j]-origin[j]) for j in range(2)),s))
        distal = ordered[driver['retained_loads']:]
        axis = max(range(2),key=lambda j:max(positions[n][j] for n,p in distal)-min(positions[n][j] for n,p in distal))
        distal.sort(key=lambda s:(positions[s[0]][axis],s))
        count = driver['proposed_buffers']; offset = 0
        for index in range(count):
            length = len(distal)//count + (index<len(distal)%count)
            sinks = distal[offset:offset+length]; offset+=length
            master = 'sg13cmos5l_buf_8' if driver['clock_branch'] else 'sg13cmos5l_buf_4'
            groups.append(dict(buffer=f"tripwire_electrical_{driver['instance']}_{index}",
                net=f"tripwire_electrical_{driver['instance']}_{index}_net",
                source_net=driver['net'],rail_source=driver['instance'],master=master,sinks=sinks,
                target=[sum(positions[n][j] for n,p in sinks)//length for j in range(2)],
                kind='clock' if driver['clock_branch'] else 'data'))
    body=re.search(r'PIN A_REN\b(.*?)END A_REN',macro_lef.read_text(),re.S)
    rect=re.search(r'RECT\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)',body[1]) if body else None
    if not rect: raise ValueError('Missing macro REN pin')
    x1,y1,x2,y2=map(float,rect.groups())
    pin=[round((12+(x1+x2)/2)*1000),round((40+191.34-(y1+y2)/2)*1000)]
    groups.append(dict(buffer='tripwire_electrical_ren',net='tripwire_electrical_ren_net',
        source_net=audit['ren']['net'],rail_source=audit['ren']['driver'][0],master='sg13cmos5l_buf_4',
        sinks=[audit['ren']['pin']],target=pin,kind='ren'))
    for group in groups:
        name=group['buffer']; width,height=sizes[group['master']]
        if name in positions or re.search(r'^\s*- '+re.escape(group['net'])+r'\s',layout,re.M):
            raise ValueError('Repeated repair name')
        distance,x,y,orient=allocate(rows,boxes,name,width,height,group['target'])
        group.update(location=[x,y,orient],target_distance_dbu=distance)
        boxes.append((name,x,y,x+width,y+height))
    for group in groups:
        width,height=sizes[group['master']];x,y,o=group['location']
        if any(n!=group['buffer'] and l<x+width and r>x and b<y+height and t>y
               for n,l,b,r,t in boxes): raise ValueError('Combined repair overlap')
    return dict(source_run=38272508875,def_sha256=DEF_SHA,groups=groups,
        added_buffers=len(groups),added_footprint_um2=sum(sizes[g['master']][0]*sizes[g['master']][1]/1e6 for g in groups),
        footprint_overlap_count=0,source_connectivity_verified=True,
        detailed_legalization_required=True,power_connectivity_verified=False,
        physical_timing_measured=False,official_signoff=False)


def validate_change(before, after, proposal):
    from event_nor2_screen import logical_cells
    old,new=logical_cells(before),logical_cells(after)
    normalize=lambda v:v.strip().removeprefix('\\')
    def normalized(cells):
        return {normalize(n):(m,tuple(sorted((p,normalize(v)) for p,v in pins))) for n,(m,pins) in cells.items()}
    old,new=normalized(old),normalized(new)
    groups=proposal['groups']; added={g['buffer'] for g in groups}
    rewires={}
    for g in groups:
        if g['buffer'] in old or any(g['net']==v for m,pins in old.values() for p,v in pins):
            raise ValueError('Repeated buffer or net')
        for n,p in g['sinks']:
            if (n,p) in rewires or dict(old[n][1]).get(p)!=g['source_net']:
                raise ValueError('Wrong or duplicated source sink')
            rewires[n,p]=g['net']
    if len(added)!=len(groups) or set(new)!=set(old)|added:
        raise ValueError('Unexpected removed or added cells')
    for n,(m,pins) in old.items():
        expected=(m,tuple(sorted((p,rewires.get((n,p),v)) for p,v in pins)))
        if new[n]!=expected: raise ValueError('Unexpected existing cell or connection change')
    for g in groups:
        if new[g['buffer']]!=(g['master'],tuple(sorted([('A',g['source_net']),('X',g['net'])]))):
            raise ValueError('Wrong identity-buffer wiring')
    return True


def target_call(layout, proposal):
    if hashlib.sha256(layout.encode()).hexdigest()!=proposal['def_sha256'] or proposal['source_run']!=38272508875:
        raise ValueError('Wrong repair source')
    components=layout.split('COMPONENTS ',1)[1].split('END COMPONENTS',1)[0]
    masters=dict(re.findall(r'^\s*- (\S+) (\S+)',components,re.M))
    entries={}
    for entry in layout.split('\nNETS ',1)[1].split('END NETS',1)[0].split(';'):
        hit=re.search(r'^\s*- (\S+)',entry)
        if hit: entries[hit[1]]=re.findall(r'\(\s*(\S+)\s+(\S+)\s*\)',entry.split(' + ',1)[0])
    def word(value):
        if not re.fullmatch(r'[A-Za-z0-9_./\[\]\-]+',value): raise ValueError('Unsafe Tcl identity')
        return '{'+value+'}'
    calls=[]
    # Group each source's complete partition into one preflighted mutation.
    for net in dict.fromkeys(g['source_net'] for g in proposal['groups']):
        groups=[g for g in proposal['groups'] if g['source_net']==net]
        master=groups[0]['master']
        if any(g['master']!=master for g in groups): raise ValueError('Mixed source masters')
        terms=entries[net]
        expectations='{'+word(net)+' {'+' '.join(word(n+'/'+p) for n,p in terms)+'} {'+ ' '.join(
            '{'+word(n)+' '+word(masters[n])+'}' for n in sorted({n for n,p in terms}))+'}}'
        serialized=[]
        for g in groups:
            values=' '.join(word(g[k]) for k in ('buffer','net','source_net','rail_source'))
            sinks=' '.join('{'+word(n)+' '+word(p)+'}' for n,p in g['sinks'])
            location=' '.join(map(str,g['location']))
            serialized.append('{'+values+' {'+location+'} {'+sinks+'}}')
        calls.append('tripwire_electrical_repair '+word(master)+' {'+expectations+'} {'+' '.join(serialized)+'}')
    return '\n'.join(calls)+'\n'


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('layout','checks','standard_lef','macro_lef'): parser.add_argument(name,type=Path)
    a=parser.parse_args()
    print(json.dumps(plan(a.layout.read_text(),a.checks.read_text(),a.standard_lef,a.macro_lef),indent=2))

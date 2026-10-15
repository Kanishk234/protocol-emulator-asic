"""Exact final-checkpoint identity-buffer plan; physical qualification required."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from electrical_load_inventory import inventory, def_identifier
from fanout_sram_plan import occupancy
from sram_bank_plan import allocate, MACRO_LEF_SHA

DEF_SHA = 'e8512f53f6f4d4c16bab1724b48f91ed9fad34ee105a11d0579ac3a8bef0e11b'


RESIDUAL_DEF_SHA = '1f037dcdee9826d876c82ecd7ce71c699e342df4fea4bb83c373ed5cc13d38a9'

FINISH_DEF_SHA = '5a436a81e547204e1ffbb73830664a8245b2844a5e3dad76ae85a2adf2188cfd'

INCREMENTAL_DEF_SHA='7626616e05699cffde246ab26e501d212a2d889d6671ed7a8186796fb49137a1'

def plan(layout, checks, std_lef, macro_lef, residual=False, finish=False, incremental=False):
    if any(type(v) is not bool for v in (residual,finish,incremental)) or sum((residual,finish,incremental))>1: raise ValueError('Invalid repair selection')
    source_sha = INCREMENTAL_DEF_SHA if incremental else (FINISH_DEF_SHA if finish else (RESIDUAL_DEF_SHA if residual else DEF_SHA))
    prefix = 'tripwire_incremental' if incremental else ('tripwire_finish' if finish else ('tripwire_residual' if residual else 'tripwire_electrical'))
    if hashlib.sha256(layout.encode()).hexdigest() != source_sha:
        raise ValueError('Wrong final electrical checkpoint')
    if hashlib.sha256(macro_lef.read_bytes()).hexdigest() != MACRO_LEF_SHA:
        raise ValueError('Wrong macro pin geometry')
    if not re.search(r'UNITS DISTANCE MICRONS 1000\b', layout):
        raise ValueError('Wrong DEF units')
    if not re.search(r'- u_chip.u_sram.sram RM_IHPSG13_1P_512x16_c2_bm_bist\s+\+ FIXED \( 12000 40000 \) FS', layout):
        raise ValueError('Wrong SRAM placement')
    audit = inventory(layout, checks, data_budget=4 if residual or finish or incremental else 6)
    sizes = {}
    boxes = None
    for master in (('sg13cmos5l_buf_4','sg13cmos5l_buf_8','sg13cmos5l_buf_1','sg13cmos5l_nor4_2') if finish else ('sg13cmos5l_buf_4','sg13cmos5l_buf_8')):
        size, occupied = occupancy(layout, std_lef, 1000, '__none__', master)
        sizes[master] = size
        if boxes is None: boxes = occupied
    rows = [(int(x),int(y),o,int(n),int(p)) for x,y,o,n,p in re.findall(
        r'^ROW \S+ CoreSite (\d+) (\d+) (N|FS) DO (\d+) BY 1 STEP (\d+) 0 ;', layout,re.M)
        if finish or incremental or int(y)>=241920]
    if finish or incremental:
        # Lower rows are usable to the right of the SRAM halo. Do not force
        # remote lower-right sinks up above the macro. Keep lower-left excluded.
        rows=[(x+max(0,(260000-x+p-1)//p)*p,y,o,n-max(0,(260000-x+p-1)//p),p)
              if y<241920 else (x,y,o,n,p) for x,y,o,n,p in rows]
        rows=[r for r in rows if r[3]>0]
    if not rows: raise ValueError('Missing legal rows')
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
            groups.append(dict(buffer=f"{prefix}_{driver['instance']}_{index}",
                net=f"{prefix}_{driver['instance']}_{index}_net",
                source_net=driver['net'],rail_source=driver['instance'],master=master,sinks=sinks,
                target=[sum(positions[n][j] for n,p in sinks)//length for j in range(2)],
                kind='clock' if driver['clock_branch'] else 'data'))
    resizes=[]
    if incremental:
        # This library has no NAND3_2. Shorten the weak NAND3 output load by
        # feeding two local BUF4s, preserving every prior functional/diode sink.
        sections=layout.split('\nNETS ',1)[1].split('END NETS',1)[0]
        entry=re.search(r'^\s*- _03831_\s+([^;]+);',sections,re.M)
        terms=re.findall(r'\(\s*(\S+)\s+(\S+)\s*\)',entry[1]) if entry else []
        sinks=sorted(p for p in terms if p!=('_28807_','Y'))
        if len(sinks)!=6 or not re.search(r'- _28807_ sg13cmos5l_nand3_1\b',layout):
            raise ValueError('Changed weak NAND3 source')
        for index in range(2):
            selected=sinks[index*3:(index+1)*3]
            groups.append(dict(buffer=prefix+'_slew'+str(index),net=prefix+'_slew_net'+str(index),
                source_net='_03831_',rail_source='_28807_',master='sg13cmos5l_buf_4',
                sinks=selected,target=list(positions['_28807_']),kind='slew-isolation'))
    elif finish:
        sections=layout.split('\nNETS ',1)[1].split('END NETS',1)[0]
        nets={}
        for entry in sections.split(';'):
            hit=re.search(r'^\s*- (\S+)',entry)
            if hit: nets[def_identifier(hit[1])]=re.findall(r'\(\s*(\S+)\s+(\S+)\s*\)',entry.split(' + ',1)[0])
        if sorted(nets.get('_00296_',[]))!=sorted([('_33530_','Y'),('_45710_','D')]):
            raise ValueError('Hold leaf changed')
        groups.append(dict(buffer=prefix+'_hold',net=prefix+'_hold_net',source_net='_00296_',
            rail_source='_45710_',master='sg13cmos5l_buf_1',sinks=[('_45710_','D')],
            target=list(positions['_45710_']),kind='hold'))
        if not re.search(r'- _25245_ sg13cmos5l_nor4_1\b',layout): raise ValueError('Wrong slew driver')
        pins={p:net for net,terms in nets.items() for n,p in terms if n=='_25245_'}
        if set(pins)!={'A','B','C','D','Y'} or pins['Y']!='_19647_': raise ValueError('Wrong NOR4 connections')
        width,height=sizes['sg13cmos5l_nor4_2']
        distance,x,y,orient=allocate(rows,boxes,'_25245_',width,height,positions['_25245_'])
        boxes=[b for b in boxes if b[0]!='_25245_']+[('_25245_',x,y,x+width,y+height)]
        resizes.append(dict(instance='_25245_',old_master='sg13cmos5l_nor4_1',new_master='sg13cmos5l_nor4_2',
            pins=pins,location=[x,y,orient],origin_displacement_dbu=distance))
    else:
        pin_name = 'A_ADDR[2]' if residual else 'A_REN'
        body=re.search(r'PIN '+re.escape(pin_name)+r'\s(.*?)END '+re.escape(pin_name),macro_lef.read_text(),re.S)
        rect=re.search(r'RECT\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)',body[1]) if body else None
        if not rect: raise ValueError('Missing macro REN pin')
        x1,y1,x2,y2=map(float,rect.groups())
        pin=[round((12+(x1+x2)/2)*1000),round((40+191.34-(y1+y2)/2)*1000)]
        source_net=audit['ren']['net']; rail_source=audit['ren']['driver'][0]
        sink=audit['ren']['pin']
        if residual:
            if not re.search(r'- place7515 sg13cmos5l_buf_1\b',layout): raise ValueError('Wrong address driver')
            entry=re.search(r'^\s*- net7515\s+([^;]+);',layout.split('\nNETS ',1)[1],re.M)
            terms=re.findall(r'\(\s*(\S+)\s+(\S+)\s*\)',entry[1]) if entry else []
            if sorted(terms)!=sorted([('place7515','X'),('u_chip.u_sram.sram','A_ADDR[2]')]):
                raise ValueError('Wrong isolated address load')
            source_net='net7515';rail_source='place7515';sink=('u_chip.u_sram.sram','A_ADDR[2]')
        groups.append(dict(buffer=prefix+('_macro' if residual else '_ren'),net=prefix+('_macro_net' if residual else '_ren_net'),
            source_net=source_net,rail_source=rail_source,master='sg13cmos5l_buf_4',
            sinks=[sink],target=pin,kind='address' if residual else 'ren'))
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
    result = dict(source_run=38294805019 if incremental else (38283838612 if finish else (38281277834 if residual else 38272508875)),def_sha256=source_sha,groups=groups,
        added_buffers=len(groups),added_footprint_um2=sum(sizes[g['master']][0]*sizes[g['master']][1]/1e6 for g in groups),
        footprint_overlap_count=0,source_connectivity_verified=True,
        detailed_legalization_required=True,power_connectivity_verified=False,
        physical_timing_measured=False,official_signoff=False)
    if finish:
        result.update(resizes=resizes,resize_added_footprint_um2=2.88*3.78)
    return result


def expanded_pins(master, pins):
    """Match known SRAM input bus bits to OpenDB's individual terminals."""
    normalize=lambda v:v.strip().removeprefix('\\')
    expanded=[]
    widths={'A_ADDR':9,'A_DIN':16}
    for pin,value in pins:
        if master=='RM_IHPSG13_1P_512x16_c2_bm_bist' and pin in widths:
            width=widths[pin];value=value.strip()
            if not value.startswith('{') or not value.endswith('}'):
                raise ValueError('Unsupported SRAM input bus representation')
            bits=value[1:-1].split(',')
            if len(bits)!=width or any(not b.strip() or '{' in b or '}' in b for b in bits):
                raise ValueError('Wrong SRAM input bus width or representation')
            expanded.extend((f'{pin}[{width-1-i}]',normalize(b)) for i,b in enumerate(bits))
        else:expanded.append((pin,normalize(value)))
    return tuple(sorted(expanded))


def validate_change(before, after, proposal):
    from event_nor2_screen import logical_cells
    old,new=logical_cells(before),logical_cells(after)
    normalize=lambda v:v.strip().removeprefix('\\')
    def normalized(cells):
        result={}
        for n,(m,pins) in cells.items():
            result[normalize(n)]=(m,expanded_pins(m,pins))
        return result
    old,new=normalized(old),normalized(new)
    for resize in proposal.get('resizes',[]):
        name=resize['instance'];master,pins=old[name]
        if (name!='_25245_' or master!='sg13cmos5l_nor4_1' or resize['old_master']!=master
                or resize['new_master']!='sg13cmos5l_nor4_2' or dict(pins)!=resize['pins']):
            raise ValueError('Unreviewed resize or changed resize connections')
        old[name]=(resize['new_master'],pins)
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
    if (hashlib.sha256(layout.encode()).hexdigest()!=proposal['def_sha256']
            or (proposal['source_run'],proposal['def_sha256']) not in
            {(38272508875,DEF_SHA),(38281277834,RESIDUAL_DEF_SHA),(38283838612,FINISH_DEF_SHA),(38294805019,INCREMENTAL_DEF_SHA)}):
        raise ValueError('Wrong repair source')
    components=layout.split('COMPONENTS ',1)[1].split('END COMPONENTS',1)[0]
    masters=dict(re.findall(r'^\s*- (\S+) (\S+)',components,re.M))
    entries={}
    for entry in layout.split('\nNETS ',1)[1].split('END NETS',1)[0].split(';'):
        hit=re.search(r'^\s*- (\S+)',entry)
        if hit: entries[def_identifier(hit[1])]=re.findall(r'\(\s*(\S+)\s+(\S+)\s*\)',entry.split(' + ',1)[0])
    def word(value):
        if not re.fullmatch(r'[A-Za-z0-9_./\[\]\-]+',value): raise ValueError('Unsafe Tcl identity')
        return '{'+value+'}'
    calls=[]
    for resize in proposal.get('resizes',[]):
        pins=' '.join(word(p)+' '+word(n) for p,n in sorted(resize['pins'].items()))
        calls.append('tripwire_size_electrical {{'+word(resize['instance'])+' '+word(resize['old_master'])+' '+word(resize['new_master'])+' {'+pins+'}}}')
        x,y,o=resize['location']
        calls.append('tripwire_place_electrical_resize '+word(resize['instance'])+' '+word(resize['new_master'])+' {'+f'{x} {y} {o}'+'}')
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

"""D-091: congestion-driven placement, no sizing or logic change, on best133 control."""
import json
import os
from pathlib import Path
import re
import subprocess
import cloud_hold_allocation as source
import cloud_delay_rebalance as shared
import cloud_cfg_fanout as cfg
import cloud_hotspot_padding as guards

ROOT=source.ROOT
OUT=ROOT/"build/congestion_reflow"
EDIT=r'''
read_db $::env(WARP_INPUT_ODB)
foreach library $::env(WARP_CELL_LIBS) {read_liberty $library}
help global_placement
write_def $::env(WARP_DEF_BEFORE)
# No timing-driven resizing, pin movement, macro movement or capacity changes.
global_placement -skip_initial_place -routability_driven -density 0.55 -overflow 0.1
detailed_placement
'''+"check_placement"+shared.EDIT.split("check_placement",1)[1]+r'''
write_def $::env(WARP_DEF)
'''


def check_rows(def_text, geometry, instances):
    rows=[]
    pattern=r"^ROW\s+\S+\s+\S+\s+(\d+)\s+(\d+)\s+(N|S|FN|FS)\s+DO\s+(\d+)\s+BY\s+1\s+STEP\s+(\d+)\s+0\s*;"
    for line in def_text.splitlines():
        if not line.startswith('ROW '):continue
        m=re.fullmatch(pattern,line)
        if not m:raise ValueError("Unsupported actual native row")
        x,y,orient,count,step=m.groups();x,y,count,step=map(int,(x,y,count,step))
        if step!=480 or count<=0:raise ValueError("Actual native row site differs")
        rows.append((x,y,x+count*step,orient))
    if not rows:raise ValueError("Missing actual native rows")
    _,_,boxes=guards.boxes(geometry)
    phase={'R0':0,'MY':0,'MX':1,'R180':1,'N':0,'FN':0,'S':1,'FS':1}
    checked=0
    for name,(kind,b) in boxes.items():
        if kind!='CORE':continue
        orient=instances[name][2]
        if orient not in phase:raise ValueError("Unsupported native cell orientation")
        matches=[row for row in rows if b[0]>=row[0] and b[2]<=row[2] and b[1]==row[1]]
        if not matches or not any(phase[orient]==phase[row[3]] for row in matches):
            raise ValueError("Cell vertical power phase differs from actual native row")
        checked+=1
    return checked


def audit_placement(before,after,old_geometry,new_geometry,old_def,def_text):
    for section in ("PINS",):
        pattern=rf"^{section}\s+\d+\s*;.*?^END {section}\s*$"
        old_match=re.search(pattern,old_def,re.M|re.S);new_match=re.search(pattern,def_text,re.M|re.S)
        if old_match is None or new_match is None or old_match.group()!=new_match.group():
            raise ValueError("Physical boundary pins changed or absent")
    if [x for x in old_def.splitlines() if x.startswith(("ROW ","DIEAREA "))] != [x for x in def_text.splitlines() if x.startswith(("ROW ","DIEAREA "))]:
        raise ValueError("Die outline or actual native rows changed")
    old,op=cfg.parse_census(before);new,np=cfg.parse_census(after)
    if set(old)!=set(new) or len(old)!=3606 or op!=np:raise ValueError("Instance/connectivity change")
    du,site,ob=guards.boxes(old_geometry);ndu,nsite,nb=guards.boxes(new_geometry)
    if (du,site,set(ob))!=(ndu,nsite,set(nb)) or set(ob)!=set(old):raise ValueError("Geometry scope differs")
    moved=[]
    for name,record in old.items():
        if record[0]!=new[name][0] or record[3]!=new[name][3]:raise ValueError("Master/status change")
        kind,b=ob[name];nkind,n=nb[name]
        if (kind,b[2]-b[0],b[3]-b[1])!=(nkind,n[2]-n[0],n[3]-n[1]):raise ValueError("Actual cell dimensions changed")
        if name=='u_fabric' and (record!=new[name] or ob[name]!=nb[name]):raise ValueError("Fixed macro changed")
        if record!=new[name] or b!=n:moved.append(name)
    if not moved:raise ValueError("No placement-policy effect")
    return {'instances':len(old),'moved_instances':moved,'masters_status_connectivity_exact':True,
        'fixed_macro_exact':True,'native_row_power_phase_cells':check_rows(def_text,new_geometry,new)}


def main():
    OUT.mkdir(exist_ok=False)
    result={'producer_passed':False,'physical_acceptance':False,'routing_executed':False,
        'source_run':38167697696,'placement_density_target':0.55,'corners':{}}
    def save():(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    save()
    try:
        for name,digest in source.EXPECTED.items():
            if cfg.sha(source.SOURCE/name)!=digest:raise ValueError('Best control differs')
        archive=ROOT/'build/fanout-preflight-source.tar.gz'
        if cfg.sha(archive)!=cfg.SOURCE_SHA:raise ValueError('Original archive differs')
        source.prepare_payload(archive,source.SOURCE/'original_source')
        config=json.loads((source.SOURCE/'config.json').read_text())
        libraries=config['LIB']['nom_fast_1p32V_m40C']
        if not libraries or any(not Path(p).is_file() or any(c.isspace() for c in p) for p in libraries):raise ValueError('Missing/unsupported pinned library paths')
        script=OUT/'placement.tcl';script.write_text(cfg.CENSUS+EDIT)
        env={'WARP_INPUT_ODB':source.SOURCE/'padded.odb','WARP_CELL_LIBS':' '.join(libraries),
            'WARP_AFTER':OUT/'after.tsv','WARP_GEOMETRY':OUT/'geometry_after.tsv',
            'WARP_DEF_BEFORE':OUT/'before.def','WARP_OUTPUT_ODB':OUT/'candidate.odb','WARP_OUTPUT_NL':OUT/'candidate.nl.v','WARP_DEF':OUT/'placement.def'}
        command=['docker','run','--rm','-v',f'{ROOT}:{ROOT}','-w',str(ROOT)]
        for key,value in env.items():command.extend(['-e',f'{key}={value}'])
        command.extend(['--entrypoint','openroad',cfg.IMAGE,'-exit',str(script)])
        with (OUT/'placement.log').open('w') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=600)
        result['audit']=audit_placement((source.SOURCE/'after.tsv').read_text(),(OUT/'after.tsv').read_text(),
            (source.SOURCE/'geometry_after.tsv').read_text(),(OUT/'geometry_after.tsv').read_text(),(OUT/'before.def').read_text(),(OUT/'placement.def').read_text());save()
        guards.OUT=OUT
        sdc=source.SOURCE/'padded_sta_nom_typ_1p20V_25C/final/sdc/tt_um_warp.sdc'
        if cfg.sha(sdc)!='2fd4e213532d83ee258899b6fc1ed48c4e5d91ddb0ccbe21eea0226cc90fd56e':raise ValueError('SDC changed')
        for corner in config['STA_CORNERS']:
            case=guards.sta(config,'candidate_'+corner,OUT/'candidate.odb',OUT/'candidate.nl.v',sdc,corner)
            if case['metrics'][f'timing__hold__ws__corner:{corner}']<0.1:raise ValueError('Original additional hold margin lost')
            result['corners'][corner]=case;save()
        for name,digest in source.EXPECTED.items():
            if cfg.sha(source.SOURCE/name)!=digest:raise ValueError('Original control modified')
        result['candidate_sha256']={n:cfg.sha(OUT/n) for n in ('candidate.odb','candidate.nl.v')}
        result['producer_passed']=True
    except Exception as exc:result['error']=str(exc);raise
    finally:save()


if __name__=='__main__':main()

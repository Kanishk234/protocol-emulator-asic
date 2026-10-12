"""Read-only mapped hold-delay allocation; no timing redundancy conclusion."""
import argparse
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
from cloud_cfg_fanout import parse_census
from cloud_hotspot_padding import boxes

DELAY="sg13cmos5l_dlygate4sd3_1"
FF="sg13cmos5l_dfrbpq_1"
MUX="sg13cmos5l_mux2_1"


def audit(census,geometry):
    instances,pins=parse_census(census.read_text())
    dbu,site,shapes=boxes(geometry.read_text())
    if set(instances)!=set(shapes) or dbu!=1000 or site!=480:
        raise ValueError("Native census/geometry scope differs")
    bycell=defaultdict(list);nets=defaultdict(list)
    for key,value in pins.items():
        if value[1] in ("POWER","GROUND") or value[-1]=="NULL":continue
        nets[value[-1]].append((key,value))
        if key[0]=="PIN":bycell[key[1].rsplit("/",1)[0]].append((key,value))
    def sources(net):
        return [(k,v) for k,v in nets[net] if (k[0]=="PIN" and v[0]=="OUTPUT") or(k[0]=="PORT" and v[0]=="INPUT")]
    def sinks(net):
        return [(k,v) for k,v in nets[net] if (k[0]=="PIN" and v[0]=="INPUT") or(k[0]=="PORT" and v[0]=="OUTPUT")]
    def role(key):
        if key[0]=="PORT":return "top_port"
        name,pin=key[1].rsplit("/",1)
        return instances[name][0]+"/"+pin
    def area(name):
        _,b=shapes[name]
        return (b[2]-b[0])*(b[3]-b[1])/(dbu*dbu)
    inputs=Counter();outputs=Counter();feedback=[];delay=[]
    for name,record in instances.items():
        if record[0]!=DELAY:continue
        entries=bycell[name]
        incoming=[v[-1] for k,v in entries if v[0]=="INPUT"]
        outgoing=[v[-1] for k,v in entries if v[0]=="OUTPUT"]
        if len(incoming)!=1 or len(outgoing)!=1:
            raise ValueError("Expected one-input/one-output delay cell")
        src=sources(incoming[0]);dst=sinks(outgoing[0])
        inputs.update(role(k) for k,v in src);outputs.update(role(k) for k,v in dst)
        delay.append(name)
        if len(src)!=1 or src[0][0][0]!="PIN":continue
        source,pin=src[0][0][1].rsplit("/",1)
        if instances[source][0]!=FF or pin!="Q":continue
        for key,v in dst:
            if key[0]!="PIN":continue
            target,pin=key[1].rsplit("/",1)
            if instances[target][0]!=MUX or pin not in ("A0","A1"):continue
            for output,ov in bycell[target]:
                if ov[0]=="OUTPUT" and any(k==("PIN",source+"/D") for k,v in sinks(ov[-1])):
                    feedback.append({"delay":name,"source_ff":source,"mux":target})
    core_area=sum(area(n) for n,(kind,_) in shapes.items() if kind=="CORE")
    delay_area=sum(area(n) for n in delay)
    return {"scope":"Mapped allocation/graph evidence, not proof any delay is removable",
        "source_sha256":{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (census,geometry)},
        "instance_count":len(instances),"delay_master":DELAY,"delay_cells":len(delay),
        "delay_bbox_area_um2":delay_area,"all_core_bbox_area_um2":core_area,
        "delay_fraction_of_core_bbox_area":delay_area/core_area,
        "input_endpoint_memberships":dict(inputs.most_common()),
        "output_endpoint_memberships":dict(outputs.most_common()),
        "direct_ff_q_delay_mux_same_ff_d_feedback":feedback}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("census",type=Path);parser.add_argument("geometry",type=Path)
    args=parser.parse_args();print(json.dumps(audit(args.census,args.geometry),indent=2))

"""Strict native OpenDB congestion grid; not a physical sign-off report."""
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
import hashlib
from pathlib import Path

LAYERS = {"Metal1", "Metal2", "Metal3", "Metal4"}


def number(text):
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise ValueError("Invalid grid number") from None
    if not value.is_finite() or value < 0:
        raise ValueError("Nonfinite or negative grid value")
    return value


def audit(path):
    rows = Path(path).read_text().splitlines()
    if len(rows) < 7:
        raise ValueError("Missing grid")
    meta = rows[0].split("\t")
    if len(meta)!=3 or meta[0]!="META":
        raise ValueError("Missing grid dimensions")
    nx,ny = map(int,meta[1:])
    if min(nx,ny)<2:
        raise ValueError("Degenerate grid")
    for line,tag,count in ((rows[1],"X",nx),(rows[2],"Y",ny)):
        fields=line.split("\t")
        if len(fields)!=2 or fields[0]!=tag:
            raise ValueError("Missing grid axis")
        coords=list(map(int,fields[1].split()))
        if len(coords)!=count or any(a>=b for a,b in zip(coords,coords[1:])):
            raise ValueError("Invalid grid axis")
    seen=set();counts=Counter();stats=defaultdict(lambda:[Decimal(0),Decimal(0),Decimal(0)])
    for line in rows[3:]:
        fields=line.split("\t")
        if len(fields)!=6 or fields[0]!="CELL" or fields[1] not in LAYERS:
            raise ValueError("Invalid grid cell")
        _,layer,x,y,capacity,usage=fields
        x,y=int(x),int(y);key=(layer,x,y)
        if not(0<=x<nx-1 and 0<=y<ny-1) or key in seen:
            raise ValueError("Duplicate/out-of-range grid cell")
        seen.add(key);counts[layer]+=1
        capacity,usage=number(capacity),number(usage)
        stats[layer][0]+=capacity;stats[layer][1]+=usage;stats[layer][2]+=max(Decimal(0),usage-capacity)
    if set(counts)!=LAYERS or any(counts[layer]!=(nx-1)*(ny-1) for layer in LAYERS):
        raise ValueError("Incomplete native grid")
    if any(stats[layer][0]==0 for layer in LAYERS):
        raise ValueError("Empty native layer capacity")
    return {"sha256":hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "dimensions":[nx,ny],"observed_cells":len(seen),
        "layers":{layer:dict(capacity=float(v[0]),usage=float(v[1]),overflow=float(v[2]))
                  for layer,v in sorted(stats.items())},
        "total_overflow":float(sum(v[2] for v in stats.values())),
        "scope":"Native OpenDB grid observation; not detailed-routing/physical acceptance"}


def guide_coverage(path, census):
    from cloud_cfg_fanout import parse_census
    _,pins=parse_census(census)
    required=Counter(v[-1] for v in pins.values() if v[-1]!="NULL" and v[1] not in ("POWER","GROUND"))
    nets={}
    for line in Path(path).read_text().splitlines():
        row=line.split("\t")
        if len(row)!=5 or row[0]!="NET" or row[1] in nets:
            raise ValueError("Invalid native guide inventory")
        terms,guides,abut=map(int,row[2:])
        if terms<0 or guides<0 or abut not in (0,1):
            raise ValueError("Invalid guide counts")
        nets[row[1]]=(terms,guides,abut)
    missing=[]
    for name,terms in required.items():
        if name not in nets or nets[name][0]!=terms:
            raise ValueError("Guide net census differs: "+name)
        if terms>1 and nets[name][1]==0 and not nets[name][2]:
            missing.append(name)
    return {"required_net_count":len(required),"missing_guides":missing,
        "sha256":hashlib.sha256(Path(path).read_bytes()).hexdigest()}

"""Place the response-lane FF through its retained driving LUT; no logic change."""
import copy
from fixed_relocation import logical_graph

BEL='X2Y1/A'


def pin_response_lane(design):
    derived=copy.deepcopy(design);m=derived['modules']['warp_top']
    bits=m['netnames']['u_user.r_lane']['bits']
    if len(bits)!=1 or type(bits[0]) is not int:raise ValueError('Require scalar response lane')
    drivers=[(n,c) for n,c in m['cells'].items() if c.get('port_directions',{}).get('O')=='output' and c['connections'].get('O')==bits]
    if len(drivers)!=1:raise ValueError('Ambiguous response-lane FF')
    ffname,ff=drivers[0]
    if (ff['type']!='LUTFF_SR' or ff['parameters'] or set(ff['connections'])!={'CLK','D','O','R'} or
            any(len(v)!=1 or type(v[0]) is not int for v in ff['connections'].values())):
        raise ValueError('Unsupported response-lane FF')
    luts=[(n,c) for n,c in m['cells'].items() if c.get('type')=='LUT4' and c['connections'].get('O')==ff['connections']['D']]
    if len(luts)!=1:raise ValueError('Require unique retained response-lane LUT')
    name,lut=luts[0]
    if any(k in c.get('attributes',{}) for c in (lut,ff) for k in ('NEXTPNR_BEL','BEL_STRENGTH')):
        raise ValueError('Response-lane placement already constrained')
    old=copy.deepcopy(lut)
    lut.setdefault('attributes',{}).update(NEXTPNR_BEL=BEL,BEL_STRENGTH=format(6,'032b'))
    if logical_graph(m)!=logical_graph(design['modules']['warp_top']):
        raise ValueError('Response-lane placement changes logic')
    return derived,dict(ff=ffname,retained_lut=name,before=old,after=copy.deepcopy(lut),
        capture_output=bits,required_bel=BEL,logical_graph_preserved=True,
        scope='One retained-LUT placement constraint; unchanged FF/data/clock/reset. Route, native function and timing remain unmeasured.')

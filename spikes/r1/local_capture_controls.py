"""Absorb only the eight SPI receive FF enable/reset functions into LUT data.

Keep LUTFF_ESR itself (including its initialization semantics) with E=1/R=0.
For every binary D,E,R,Q, new D = E ? (R ? 0 : D) : Q. Clock/output and
all other cells stay intact. This is not a routing or timing acceptance.
"""
import copy
import hashlib
import re

INIT=0x3B08
ESR_SHA='7418b6bbfc9d9d3d756567a4b5cdf1767c443ee199022b47e58b29337ee11b25'


def vendor_semantics(text):
    matches=re.findall(r'module LUTFF_ESR\b.*?endmodule',text,re.S)
    if len(matches)!=1 or hashlib.sha256(matches[0].encode()).hexdigest()!=ESR_SHA:
        raise ValueError('Unsupported vendor LUTFF_ESR semantics')
    return ESR_SHA


def absorb_capture(design):
    derived=copy.deepcopy(design);m=derived['modules']['warp_top']
    bits=m['netnames']['u_user.srdata']['bits']
    if len(bits)!=8 or len(set(bits))!=8 or any(type(b) is not int for b in bits):
        raise ValueError('Require eight unique SPI receive output bits')
    if any(n.startswith('wp_spi_capture_local_') for n in m['cells']):
        raise ValueError('Capture controls already transformed')
    targets=[]
    for bit in bits:
        drivers=[(n,c) for n,c in m['cells'].items()
                 if c.get('port_directions',{}).get('O')=='output' and c['connections'].get('O')==[bit]]
        if len(drivers)!=1:raise ValueError('Ambiguous SPI capture driver')
        name,cell=drivers[0]
        if (cell['type']!='LUTFF_ESR' or cell['parameters'] or
                set(cell['connections'])!={'CLK','D','E','R','O'} or
                any(len(v)!=1 or type(v[0]) is not int for v in cell['connections'].values()) or
                cell['port_directions']!={'CLK':'input','D':'input','E':'input','R':'input','O':'output'}):
            raise ValueError('Unsupported SPI capture FF shape or semantics')
        targets.append((name,cell))
    if len({tuple(c['connections']['CLK']) for n,c in targets})!=1:
        raise ValueError('Capture clocks differ')
    for p in ('E','R'):
        if len({tuple(c['connections'][p]) for n,c in targets})!=1:
            raise ValueError('Capture controls differ')
    used=[b for c in m['cells'].values() for v in c['connections'].values() for b in v if type(b) is int]
    used += [b for n in m['netnames'].values() for b in n['bits'] if type(b) is int]
    used += [b for p in m.get('ports',{}).values() for b in p['bits'] if type(b) is int]
    fresh=max(used)+1;changes=[]
    for index,(name,cell) in enumerate(targets):
        before=copy.deepcopy(cell);pins=cell['connections'];newbit=fresh+index
        lutname='wp_spi_capture_local_'+str(index)
        lut=dict(type='LUT4',hide_name=0,parameters={'INIT':format(INIT,'016b')},
            attributes={},port_directions={'I0':'input','I1':'input','I2':'input','I3':'input','O':'output'},
            connections={'I0':list(pins['D']),'I1':list(pins['E']),'I2':list(pins['R']),
                         'I3':list(pins['O']),'O':[newbit]})
        m['cells'][lutname]=lut;m['netnames'][lutname]={'hide_name':0,'bits':[newbit],'attributes':{}}
        pins.update(D=[newbit],E=['1'],R=['0'])
        changes.append(dict(ff=name,before=before,after=copy.deepcopy(cell),lut=copy.deepcopy(lut)))
    return derived,dict(changed_flip_flops=8,added_logical_luts=8,binary_transitions_per_ff=16,
        unchanged_ff_type='LUTFF_ESR',vendor_cell_sha256=ESR_SHA,changes=changes,
        scope='Same clock/output/FF primitive; binary next-state equality. No fit, native/reload or timing claim.')

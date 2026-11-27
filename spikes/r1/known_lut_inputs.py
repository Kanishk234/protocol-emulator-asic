"""Route logically unused LUT inputs to the existing input reset net.

Only user-netlist LUTs change; clocks, sequential cells, hard primitives and
the physical fabric stay intact. Per-cell binary equality is exhaustive.
Native initialization and routed timing still require separate qualification.
"""
import copy
import re


def expand_truth(init,width,connections,indices):
    if not isinstance(init,str) or len(init)!=1<<width or set(init)-{'0','1'}:
        raise ValueError('Require a complete binary LUT truth table')
    truth=int(init,2)
    for i in indices:
        bits=connections.get('I'+str(i),[])
        if len(bits)>1:raise ValueError('Non-scalar LUT input')
        if not bits or bits[0] not in ('0','1') and not isinstance(bits[0],int):
            if i<width and any((truth>>a&1)!=(truth>>(a^(1<<i))&1) for a in range(1<<width)):
                raise ValueError('Unconnected LUT input affects the function')
    result=0
    for a in range(16):
        old=0
        for i in range(width):
            bits=connections.get('I'+str(i),[])
            value=int(bits[0]) if bits and bits[0] in ('0','1') else a>>i&1
            old|=value<<i
        result|=(truth>>old&1)<<a
    return format(result,'016b')


def fill_inputs(design):
    filled=copy.deepcopy(design);module=filled['modules']['warp_top']
    reset=module['netnames']['u_user.rst_n']['bits']
    if len(reset)!=1 or type(reset[0]) is not int:raise ValueError('Require one existing input reset net')
    drivers=[c for c in module['cells'].values() for p,d in c.get('port_directions',{}).items()
             if d=='output' and c['connections'].get(p)==reset]
    if (len(drivers)!=1 or drivers[0]['type']!='IOBUF' or
            drivers[0]['connections'].get('EN')!=['0'] or drivers[0]['connections'].get('IN')!=['0']):
        raise ValueError('Reset must come from the existing input-only IOBUF')
    changes=[]
    for name,cell in module['cells'].items():
        match=re.fullmatch(r'LUT([1-4])',cell['type']);ha=cell['type']=='LUT4_HA'
        if not match and not ha:continue
        width=int(match[1]) if match else 4
        indices=[3] if ha else list(range(4))
        ports=cell['connections'];before=copy.deepcopy(cell)
        if set(cell['parameters'])-({'INIT','I0MUX'} if ha else {'INIT'}):
            raise ValueError('Unsupported LUT parameters')
        for i in range(4):
            bits=ports.get('I'+str(i),[])
            if len(bits)>1 or bits and type(bits[0]) is not int and bits[0] not in ('0','1','x','z'):
                raise ValueError('Unsupported LUT input encoding')
        replacement=[i for i in indices if not ports.get('I'+str(i)) or
                     ports['I'+str(i)][0] in ('0','1','x','z')]
        if not replacement and width==4:continue
        new_init=expand_truth(cell['parameters']['INIT'],width,ports,indices)
        for i in replacement:
            if any((int(new_init,2)>>a&1)!=(int(new_init,2)>>(a^(1<<i))&1) for a in range(16)):
                raise ValueError('Rewritten input is not binary-independent')
        # HA carry uses I1/I2/Ci. Only I3 may change; preserve every other pin/mode.
        if ha:
            if not replacement:continue
            if any((int(new_init,2)>>a&1)!=(int(new_init,2)>>(a^8)&1) for a in range(16)):
                raise ValueError('HA unused-input rewrite is not independent')
        for i in replacement:
            ports['I'+str(i)]=list(reset);cell['port_directions']['I'+str(i)]='input'
        cell['type']='LUT4_HA' if ha else 'LUT4';cell['parameters']['INIT']=new_init
        changes.append(dict(cell=name,before=before,after=copy.deepcopy(cell),
                            truth_addresses_checked=16,replaced_inputs=replacement))
    if not changes:raise ValueError('No unused LUT inputs were rewritten')
    return filled,dict(reset_net=reset,changes=changes,changed_cells=len(changes),
        scope='Binary-equivalent logical LUT promotion/constant cofactoring only. No native, timing or physical acceptance.')

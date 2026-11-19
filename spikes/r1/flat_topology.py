"""Check exported flat Verilog against independent physical source inventories."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

from run_timing import same_topology


def expected_module(inventory,port_shapes):
    cells={}
    for name,master,*geometry in inventory['cells']:
        if name in cells:raise ValueError('Duplicate physical source cell')
        cells[name]=dict(type=master,connections={})
    for cell,pin,net in inventory['terms']:
        if cell not in cells:raise ValueError('Unknown physical source terminal')
        if pin in ('VDD','VSS'):
            if net!=('VPWR' if pin=='VDD' else 'VGND'):
                raise ValueError('Wrong physical source supply binding')
            continue
        if pin in cells[cell]['connections']:raise ValueError('Duplicate physical source terminal')
        cells[cell]['connections'][pin]=[net]
    ports={};seen=set()
    for name,p in port_shapes.items():
        bits=[]
        if p.get('offset',0) or p.get('upto',0):raise ValueError('Unexpected source port indexing')
        for i in range(len(p['bits'])):
            scalar=name if len(p['bits'])==1 else f'{name}[{i}]'
            if scalar not in inventory['ports']:raise ValueError('Missing physical source port')
            bits.append(inventory['ports'][scalar]);seen.add(scalar)
        ports[name]=dict(direction=p['direction'],bits=bits)
    if seen!=set(inventory['ports'])-{'VPWR','VGND'}:
        raise ValueError('Physical source signal port census differs')
    return dict(cells=cells,ports=ports)


def verify(inventory,port_shapes,exported):
    expected=expected_module(inventory,port_shapes)
    same_topology(expected,exported)
    census=Counter(c['type'] for c in exported['cells'].values())
    return dict(passed=True,cells=len(exported['cells']),configuration_latches=census['sg13cmos5l_dlhq_1'],
                edge_registers=census['sg13cmos5l_dfrbpq_1'],
                scope='Exact standard-cell masters and complete signal-net partitions versus physical source inventories. No behavioral, RC annotation or timing acceptance.')


def verilog_id(name):
    if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_$]*',name):return name
    if not name or any(c.isspace() for c in name):raise ValueError('Invalid physical netlist identifier')
    return '\\'+name+' '


def render(inventory,port_shapes,powered=False):
    """Regenerate an analysis view with explicit input and output aliases.

    OpenROAD's input alias omission is retained as a failed separate control.
    Native DEF, GDS, SPEF, standard cells and configuration storage do not change.
    """
    expected=expected_module(inventory,port_shapes);ports=expected['ports']
    if powered:
        ports.update({p:dict(direction='inout',bits=[p]) for p in ('VPWR','VGND')})
        for cell,pin,net in inventory['terms']:
            if pin in ('VDD','VSS'):expected['cells'][cell]['connections'][pin]=[net]
    lines=['`default_nettype none','module warp_r1_candidate ('+', '.join(verilog_id(p) for p in ports)+');']
    for name,p in ports.items():
        size='' if len(p['bits'])==1 else f'[{len(p["bits"])-1}:0] '
        lines.append(p['direction']+' '+size+verilog_id(name)+';')
    nets={b for c in expected['cells'].values() for bs in c['connections'].values() for b in bs}
    nets.update(b for p in ports.values() for b in p['bits'])
    lines.extend('wire '+verilog_id(n)+';' for n in sorted(nets))
    for name,p in ports.items():
        for i,net in enumerate(p['bits']):
            pin=verilog_id(name)+(f'[{i}]' if len(p['bits'])>1 else '')
            wire=verilog_id(net)
            if p['direction']=='input':lines.append('assign '+wire+' = '+pin+';')
            elif p['direction']=='output':lines.append('assign '+pin+' = '+wire+';')
            elif powered and name in ('VPWR','VGND') and net==name:continue
            else:raise ValueError('Unsupported physical analysis port direction')
    for name,c in sorted(expected['cells'].items()):
        connections=', '.join('.'+verilog_id(p)+'('+verilog_id(bs[0])+')' for p,bs in sorted(c['connections'].items()))
        lines.append(verilog_id(c['type'])+' '+verilog_id(name)+' ('+connections+');')
    return '\n'.join(lines+['endmodule','`default_nettype wire',''])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('inventory','source-top','exported','out'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args()
    result=verify(json.loads(args.inventory.read_text()),json.loads(args.source_top.read_text())['ports'],
                  json.loads(args.exported.read_text())['modules']['warp_r1_candidate'])
    args.out.write_text(json.dumps(result,indent=2)+'\n')

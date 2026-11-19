"""Represent the original proven schematic as SPICE, with all root pins intact."""
import json
from pathlib import Path
import re

from assembly_catalog import sha
from flat_reference import normalize_cells
from flat_topology import verify


def logical_lines(text):
    rows=[]
    for line in text.splitlines():
        line=line.strip()
        if not line or line.startswith('*'):continue
        if line.startswith('+'):
            if not rows:raise ValueError('Orphan SPICE continuation')
            rows[-1]+=' '+line[1:].strip()
        else:rows.append(line)
    return rows


def model_ports(text):
    result={}
    for row in logical_lines(text):
        tokens=row.split()
        if tokens[0].lower()!='.subckt':continue
        if len(tokens)<3 or tokens[1] in result or len(tokens[2:])!=len(set(tokens[2:])):
            raise ValueError('Ambiguous original SPICE model ports')
        result[tokens[1]]=tokens[2:]
    return result


def scalars(shapes):
    result=[]
    for name,p in shapes.items():
        if p.get('offset',0) or p.get('upto',0):raise ValueError('Unexpected source port indexing')
        result.extend(name if len(p['bits'])==1 else f'{name}[{i}]' for i in range(len(p['bits'])))
    return result


def render(module,models):
    ports=scalars(module['ports'])+['VPWR','VGND'];roots={}
    for name,p in module['ports'].items():
        for i,bit in enumerate(p['bits']):
            if bit in roots:raise ValueError('Cannot discard an original root alias')
            roots[bit]=name if len(p['bits'])==1 else f'{name}[{i}]'
    if len(ports)!=449 or len(set(ports))!=449:raise ValueError('Incomplete original root interface')
    def node(bit):
        if type(bit) is not int:raise ValueError('Unexpected schematic literal/configuration constant')
        return roots.get(bit,'n'+str(bit))
    lines=['* Original source-equivalent schematic; no extracted signal data.']
    for i in range(0,len(ports),8):
        lines.append(('.subckt warp_r1_candidate ' if i==0 else '+ ')+' '.join(ports[i:i+8]))
    for name,c in sorted(module['cells'].items()):
        pins=models.get(c['type'])
        if (not pins or set(pins)-{'VDD','VSS'}!=set(c['connections'])
                or not {'VDD','VSS'}<=set(pins)):
            raise ValueError('Original device model and schematic terminals differ')
        values={}
        for pin,bits in c['connections'].items():
            if len(bits)!=1:raise ValueError('Non-scalar standard-cell pin')
            values[pin]=node(bits[0])
        values.update(VDD='VPWR',VSS='VGND')
        tokens=['X'+name,*[values[p] for p in pins],c['type']]
        if any(not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_./\[\]$!#-]*',v) for v in tokens):
            raise ValueError('Unsafe SPICE schematic identifier')
        lines.append(' '.join(tokens))
    return '\n'.join(lines+['.ends warp_r1_candidate',''])


def parse_and_verify(text,models,inventory,shapes):
    rows=logical_lines(text);header=rows[0].split();ports=header[2:]
    if header[:2]!=['.subckt','warp_r1_candidate'] or set(ports)!=set(scalars(shapes)+['VPWR','VGND']) or len(ports)!=449:
        raise ValueError('Changed SPICE root interface')
    cells={}
    for row in rows[1:-1]:
        tokens=row.split();name=tokens[0][1:];master=tokens[-1];pins=models.get(master)
        if not tokens[0].startswith('X') or name in cells or pins is None or len(tokens[1:-1])!=len(pins):
            raise ValueError('Changed SPICE source device inventory')
        conns=dict(zip(pins,tokens[1:-1]))
        if conns.pop('VDD',None)!='VPWR' or conns.pop('VSS',None)!='VGND':
            raise ValueError('Changed original source power binding')
        cells[name]=dict(type=master,connections={p:[n] for p,n in conns.items()})
    if rows[-1]!='.ends warp_r1_candidate':raise ValueError('Incomplete SPICE schematic')
    grouped={name:dict(direction=p['direction'],bits=[name if len(p['bits'])==1 else f'{name}[{i}]'
             for i in range(len(p['bits']))]) for name,p in shapes.items()}
    return verify(inventory,shapes,dict(ports=grouped,cells=cells))


def prepare(proof,inventory,spice_models,out):
    proof,inventory,spice_models,out=(Path(p).resolve() for p in (proof,inventory,spice_models,out))
    evidence=json.loads((proof/'proof.json').read_text());physical=json.loads(inventory.read_text())
    if not evidence['passed'] or sha(proof/'powered.v')!=evidence['powered_sha256']:
        raise ValueError('Require independently source-proven schematic')
    source=json.loads((proof/'source.json').read_text())['modules']['warp_r1_candidate']
    tiles=sorted({row[0].split('/')[0] for row in physical['cells']})
    if len(tiles)!=40:raise ValueError('Incomplete original source grid')
    source=normalize_cells(source,tiles);original=verify(physical,source['ports'],source)
    models=model_ports(spice_models.read_text());text=render(source,models)
    converted=parse_and_verify(text,models,physical,source['ports'])
    if original!=converted or converted['cells']!=45429 or converted['configuration_latches']!=8736 or converted['edge_registers']!=370:
        raise ValueError('Source SPICE conversion changed resources')
    # Removing a real configuration latch must be rejected by the independent graph.
    lines=text.splitlines();victim=next(i for i,l in enumerate(lines) if l.startswith('X') and l.endswith(' sg13cmos5l_dlhq_1'))
    try:parse_and_verify('\n'.join(lines[:victim]+lines[victim+1:]),models,physical,source['ports'])
    except ValueError:negative=True
    else:raise ValueError('Missing configuration-latch control was not detected')
    out.mkdir(parents=True,exist_ok=False);path=out/'source.spice';path.write_text(text)
    result=dict(passed=True,source=original,converted=converted,root_ports=449,
                missing_device_control_detected=negative,spice_sha256=sha(path),
                input_sha256={str(p):sha(p) for p in [Path(__file__),proof/'proof.json',proof/'source.json',proof/'powered.v',inventory,spice_models]},
                scope='Independent original schematic signal partitions and every original device/power/root pin preserved in SPICE representation. Not LVS, geometry or timing acceptance.')
    (out/'proof.json').write_text(json.dumps(result,indent=2)+'\n')
    return path


def substitute_schematic_input(script,powered,schematic):
    old=f'readnet verilog {powered} $circuit2'
    if script.count(old)!=1 or script.count('\nlvs ')!=1:
        raise ValueError('Unexpected generated LVS comparison script')
    return script.replace(old,f'readnet spice {schematic} $circuit2')

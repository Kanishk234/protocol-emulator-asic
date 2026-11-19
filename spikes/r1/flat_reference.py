"""Prove a flat analysis/schematic view against the original context netlists."""
import json
from pathlib import Path
import subprocess

from assemble import NAME,top_netlist
from assembly_catalog import sha
from flat_topology import render,verify
from run_timing import LIB_SHA


def normalize_cells(module,tiles):
    result={}
    for name,cell in module['cells'].items():
        prefixes=[t for t in tiles if name.startswith(t+'.')]
        if len(prefixes)!=1:raise ValueError('Unexpected flattened source instance name')
        tile=prefixes[0];target=tile+'/'+name[len(tile)+1:]
        if target in result:raise ValueError('Duplicate flattened source cell')
        result[target]=cell
    return dict(module,cells=result)


def prepare_and_verify(source,inventory,liberty,out):
    source,inventory,liberty,out=(Path(p).resolve() for p in (source,inventory,liberty,out))
    if sha(liberty)!=LIB_SHA:raise ValueError('Require the pinned original slow library')
    out.mkdir(parents=True,exist_ok=False)
    top_path=source/'top.json';catalog_path=source/'catalog.json'
    top=json.loads(top_path.read_text());catalog=json.loads(catalog_path.read_text())
    original=[]
    for case,c in catalog['contexts'].items():
        path=source/'contexts'/case/(c['planned_master']+'.nl.v')
        if not path.is_file():raise ValueError('Missing original functional context netlist')
        original.append(path)
    physical=json.loads(inventory.read_text())
    inputs=[Path(__file__),Path(__file__).with_name('flat_topology.py'),Path(__file__).with_name('assemble.py'),
            Path(__file__).with_name('run_timing.py'),inventory,liberty,top_path,catalog_path,*original]
    frozen={str(p):sha(p) for p in inputs}
    (out/'source.v').write_text(top_netlist(top,catalog['instances'],powered=False))
    (out/'analysis.v').write_text(render(physical,top['ports']))
    (out/'powered.v').write_text(render(physical,top['ports'],powered=True))
    proofs={}
    for name in ('source','analysis'):
        lines=['read_liberty -lib -ignore_miss_func '+json.dumps(str(liberty))]
        if name=='source':lines.extend('read_verilog '+json.dumps(str(p)) for p in original)
        lines.extend(['read_verilog '+json.dumps(str(out/(name+'.v'))),'hierarchy -check -top '+NAME])
        if name=='source':lines.append('flatten -noscopeinfo')
        lines.append('write_json '+json.dumps(str(out/(name+'.json'))))
        script=out/(name+'.ys');script.write_text('\n'.join(lines)+'\n')
        with (out/(name+'.log')).open('w') as log:
            subprocess.run(['yosys','-Q','-T','-s',str(script)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
        module=json.loads((out/(name+'.json')).read_text())['modules'][NAME]
        if name=='source':module=normalize_cells(module,list(top['cells']))
        proofs[name]=verify(physical,top['ports'],module)
        if proofs[name]['cells']!=45429 or proofs[name]['configuration_latches']!=8736 or proofs[name]['edge_registers']!=370:
            raise ValueError('Original native reference resource census differs')
    if any(sha(p)!=d for p,d in frozen.items()):raise ValueError('Original schematic source changed during proof')
    result=dict(passed=True,proofs=proofs,input_sha256=frozen,
                analysis_sha256=sha(out/'analysis.v'),powered_sha256=sha(out/'powered.v'),
                scope='Exact complete source schematic and derived flat signal partitions versus independent physical inventories; explicit original supply bindings added only to powered reference. No geometry/timing or physical enclosing-grid acceptance.')
    (out/'proof.json').write_text(json.dumps(result,indent=2)+'\n')
    return out/'powered.v'

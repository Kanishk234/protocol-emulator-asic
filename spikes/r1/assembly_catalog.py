"""Read-only physical context catalog; emits no layout and grants no chip acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
WIDTHS = (47520,154080,164640,154080,154080,164640,154080,68640)
HEIGHTS = (56700,185220,185220,185220,56700)
GRAPH_SHA = '075672b468c2a2caacdd82fad6b1efef1740f09892abce1f29960b9b8991d3cb'
GATES = ('route__drc_errors','design__critical_disconnected_pin__count',
         'antenna__violating__nets','antenna__violating__pins','magic__drc_error__count',
         'klayout__drc_error__count','design__lvs_error__count')
REPORTS = [('r1_finished_lut0_44402764510.json',44402764510,'lut0'),
           ('r1_representative_physical_44445288959.json',44445288959,None),
           ('r1_wire_corner_44447843126.json',44447843126,None),
           ('r1_finished_columns_44450213740.json',44450213740,None),
           ('r1_finished_primitive_44454944540.json',44454944540,None)]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def specifications():
    result = dict(west_io=('W_IO4',0,185220),northwest=('NW_term',0,56700),
        southwest=('SW_term',0,56700),primitive1=('PRIM2T2S',2,185220),
        primitive4=('PRIM2T2S',5,185220),east_io=('E_IO4',7,185220),
        northeast=('NE_term',7,56700),southeast=('SE_term',7,56700))
    for i in range(6):
        result['lut'+str(i)] = ('LUT4x8_ha',i+1,185220)
        result['north'+str(i)] = ('N_IO',i+1,56700)
        result['south'+str(i)] = ('S_IO2',i+1,56700)
    return result


def catalog(top, rows):
    specs = specifications(); admitted = {}
    for row in rows:
        case = row['case']
        if case not in specs or case in admitted or row.get('passed') is not True:
            raise ValueError('Unknown, duplicate or failed context')
        gates = row.get('physical_gate_metrics',{})
        if any(type(gates.get(k)) not in (int,float) or gates[k] != 0 for k in GATES):
            raise ValueError('Missing or nonzero physical gate')
        if any(not re.fullmatch(r'[0-9a-f]{64}', row.get(k,'')) for k in ('gds_sha256','odb_sha256','nl_sha256')):
            raise ValueError('Missing exact qualified view hash')
        admitted[case] = dict(row,source_master=specs[case][0],planned_master='wp_r1_'+case,
                             width_dbu=WIDTHS[specs[case][1]],height_dbu=specs[case][2])
    if set(admitted) != set(specs) or len(top['cells']) != 40:
        raise ValueError('Incomplete physical context or grid census')
    instances = [];used = set();positions = set()
    for name, cell in sorted(top['cells'].items()):
        match = re.fullmatch(r'Tile_X([0-7])Y([0-4])_.+',name)
        if match is None:
            raise ValueError('Unexpected grid instance name')
        x,y = map(int,match.groups())
        if (x,y) in positions:
            raise ValueError('Duplicate grid position')
        positions.add((x,y))
        candidates = [n for n,s in specs.items() if s == (cell['type'],x,HEIGHTS[y])]
        if len(candidates) != 1:
            raise ValueError('No unique qualified physical context')
        case = candidates[0];used.add(case)
        # FABulous numbers rows from north to south; physical Y grows upward.
        instances.append(dict(instance=name,context=case,planned_master=admitted[case]['planned_master'],
                              origin_dbu=[sum(WIDTHS[:x]),sum(HEIGHTS[y+1:])]))
    if used != set(specs):
        raise ValueError('Qualified context not represented in actual grid')
    return dict(preflight_passed=True,leaf_contexts=26,grid_instances=40,
        dbu_per_um=1000,macro_size_dbu=[sum(WIDTHS),sum(HEIGHTS)],contexts=admitted,instances=instances,
        geometry_written=False,assembly_acceptance=False,timing_acceptance=False,
        scope='Read-only catalog and planned context master names. GDS/LEF renaming, shared-cell collision checks, stitching, macro DRC/LVS, shell and configured timing are not performed.')


def prepare(capsule,out):
    graph = Path(capsule)/'mapped/input/connections.json';out = Path(out)
    if sha(graph) != GRAPH_SHA:
        raise ValueError('Frozen physical graph changed')
    paths = [Path(__file__),graph];rows=[]
    for filename,run,default_case in REPORTS:
        path=ROOT/'docs/reports'/filename;paths.append(path);data=json.loads(path.read_text())
        if data['run'] != run:
            raise ValueError('Wrong finishing receipt producer')
        for row in data.get('results',[data]):
            if row.get('passed') is not True:
                # Original northeast failure stays recorded; corrected receipt is separate.
                if run != 44445288959 or row.get('case') != 'northeast':
                    raise ValueError('Unexpected failed finishing receipt')
                continue
            rows.append(dict(row,case=row.get('case',default_case),source_run=run))
    result=catalog(json.loads(graph.read_text())['modules']['eFPGA'],rows)
    result['input_sha256']={str(p):sha(p) for p in paths}
    if out.exists():
        raise ValueError('Refusing to overwrite an existing assembly catalog')
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n')


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capsule',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    prepare(**vars(p.parse_args()))

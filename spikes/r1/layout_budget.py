"""Static geometry/power screen; never substitutes for native physical gates."""
import argparse
from decimal import Decimal
import json
from pathlib import Path
from physical_route import RESERVE_COLUMNS,reserve_geometry
from physical_preflight import sha

D=lambda value:Decimal(str(value))


def describe(west,columns,east=68.64):
    widths=[D(west),*map(D,columns),D(east)]
    if len(widths)!=8 or any(w<=D('5.76') or w%D('.48') for w in widths):
        raise ValueError('Layout must have eight positive site-aligned columns with a placeable core')
    offset=D(0);power=[];pitch=D('109.92')
    for index,width in enumerate(widths):
        center=(D(12)-offset)%pitch
        if center<0:center+=pitch
        pairs=[]
        while center+D('4.1')+D('1.05')<=width-D('2.88'):
            if center-D('1.05')>=D('2.88'):pairs.append([str(center),str(center+D('4.1'))])
            center+=pitch
        power.append(dict(column=index,origin_um=str(offset),width_um=str(width),full_core_power_pairs_um=pairs))
        offset+=width
    origin_x=D('121.44');origin_y=D('30.24');height=D('669.06')
    edge=origin_x+offset;core_right=D('1286.4')
    chip_pairs=[];center=D('23.52')
    while center+D('5.15')<=core_right:
        if center-D('1.05')>=edge:chip_pairs.append([str(center),str(center+D('4.1'))])
        center+=pitch
    fits=origin_x>=D('2.88') and edge<=core_right and origin_y>=D('3.78') and origin_y+height<=D('706.86')
    return dict(column_widths_um=[str(w) for w in widths],macro_width_um=str(offset),macro_height_um=str(height),
                macro_origin_um=[str(origin_x),str(origin_y)],east_channel_um=str(core_right-edge),
                column_power=power,unpowered_columns=[p['column'] for p in power if not p['full_core_power_pairs_um']],
                chip_east_full_power_pairs_um=chip_pairs,geometric_chip_fit=fits,
                static_power_gate=bool(fits and chip_pairs and all(p['full_core_power_pairs_um'] for p in power)),
                physical_acceptance=False,timing_acceptance=False)


def layouts():
    original=describe(68.64,(154.08,)*6)
    grown=describe(68.64,RESERVE_COLUMNS)
    reclaimed=D('68.64')-(sum(map(D,RESERVE_COLUMNS))-D('154.08')*6)
    balanced=describe(reclaimed,RESERVE_COLUMNS)
    if balanced['macro_width_um']!=original['macro_width_um']:raise ValueError('Reallocation changed outer footprint')
    return dict(original_uniform=original,primitive_leaf_growth=grown,reallocated_west=balanced,
                primitive_width_derivation=reserve_geometry())


def run(evidence,out):
    evidence,out=Path(evidence).resolve(),Path(out).resolve()
    manifest=json.loads((evidence/'input/manifest.json').read_text());native=json.loads((evidence/'native/result.json').read_text())
    if not native['passed'] or native['run']!='40013513454':raise ValueError('Require accepted all-type source')
    if native['input_manifest_sha256']!=sha(evidence/'input/manifest.json'):raise ValueError('Changed manifest')
    if any(sha(evidence/'input'/name)!=digest for name,digest in manifest['files'].items()):raise ValueError('Changed prepared input')
    report=layouts();west=D(report['reallocated_west']['column_widths_um'][0]);census={}
    for tile in ('W_IO4','NW_term','SW_term'):
        row=native['cases'][tile+'-width154_08'];height=D('56.70') if tile.endswith('term') else D('185.22')
        core=(west-D('5.76'))*(height-D('7.56'))
        outputs=sum(len(p['bits']) for p in manifest['tiles'][tile]['ports'].values() if p['direction']=='output')
        estimated=D(row['cell_area_dbu2'])/D(1000000)+outputs*D('7.2576')
        census[tile]=dict(core_um2=str(core),one_buffer_per_output_area_um2=str(estimated),output_bits=outputs,
                          model_capacity_gate=estimated<core)
    report.update(source_run='40013513454',source_manifest_sha256=sha(evidence/'input/manifest.json'),
                  west_census=census,scope='Static arithmetic only. Buffer model assumes at most one fixed buf_1 per output; native pin-density/routability reserve and all changed leaf/interface gates remain unqualified.')
    out.mkdir(parents=True,exist_ok=False);(out/'budget.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();run(a.evidence,a.out)

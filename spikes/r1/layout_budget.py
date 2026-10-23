"""Static geometry/power screen; never substitutes for native physical gates."""
import argparse
from decimal import Decimal, ROUND_CEILING
import json
from pathlib import Path
from physical_preflight import sha

RESERVE_COLUMNS=(154.08,164.64,154.08,154.08,164.64,154.08)


def reserve_geometry():
    # Round native three-decimal reports upward, then include the largest
    # observed reference routability inflation at unchanged 96% density.
    required=(Decimal('26853.447')+Decimal('225.661'))/(Decimal('.96')*Decimal('177.66'))+Decimal('5.76')
    width=(required/Decimal('.48')).to_integral_value(rounding=ROUND_CEILING)*Decimal('.48')
    return dict(width_um=str(width),required_width_um=str(required),
                column_widths=list(RESERVE_COLUMNS),macro_width_um=str(Decimal('137.28')+sum(map(lambda w:Decimal(str(w)),RESERVE_COLUMNS))),
                source_run='40014699181',pin_adjusted_area_upper_um2='26853.447',routing_inflation_upper_um2='225.661')


D=lambda value:Decimal(str(value))
CRITICAL_CASES=('west_io','northwest','southwest','primitive1','primitive4')
REMAINING_CASES=('northeast','east_io','southeast',
                 *('lut'+str(i) for i in range(6)),*('north'+str(i) for i in range(6)),
                 *('south'+str(i) for i in range(6)))
BALANCED_CASES=CRITICAL_CASES+REMAINING_CASES


def balanced_geometry(x,y):
    if x not in range(8) or y not in range(5):raise ValueError('Position outside frozen grid')
    layout=layouts()['reallocated_west']
    return float(layout['column_widths_um'][x]),56.70 if y in (0,4) else 185.22


def balanced_case(name):
    declared={'west_io':('W_IO4',0,1),'northwest':('NW_term',0,0),
              'southwest':('SW_term',0,4),'primitive1':('PRIM2T2S',2,2),
              'primitive4':('PRIM2T2S',5,2),'east_io':('E_IO4',7,1),
              'northeast':('NE_term',7,0),'southeast':('SE_term',7,4)}
    for i in range(6):
        declared['lut'+str(i)]=('LUT4x8_ha',i+1,1)
        declared['north'+str(i)]=('N_IO',i+1,0)
        declared['south'+str(i)]=('S_IO2',i+1,4)
    if name not in declared:raise ValueError('Undeclared balanced-layout case')
    tile,x,y=declared[name];layout=layouts()['reallocated_west'];w,h=balanced_geometry(x,y)
    phase=layout['column_power'][x]['full_core_power_pairs_um'][0][0]
    return dict(name=name,tile=tile,x=x,y=y,width=w,height=h,center_um=phase,
                core_offset_um=str(D(phase)-D('2.88')),pitch_um='109.92',
                macro_width_um=layout['macro_width_um'],wire_only=tile=='NE_term')


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

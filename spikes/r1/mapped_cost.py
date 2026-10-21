"""Matched mapped LUT-tile cell cost, not placed area or chip routability."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_cells(cells, expected_latches):
    unknown = {name for name in cells if name != '$scopeinfo'
               and not name.startswith('sg13cmos5l_')}
    if unknown:
        raise ValueError('Unmapped cell types: '+str(sorted(unknown)))
    if cells.get('sg13cmos5l_dlhq_1',0) != expected_latches:
        raise ValueError('Configuration storage count changed')


def run(model, pdk, out, tile='LUT4x8_ha'):
    model, pdk, out = (Path(p).resolve() for p in (model,pdk,out))
    manifest = model/'resource-control.json'
    description = json.loads(manifest.read_text())
    if description['passed'] is not True or description['physical_candidate'] is not False:
        raise ValueError('Require qualified experimental model')
    for name, expected in description['generated_sha256'].items():
        if sha(model/name) != expected:
            raise ValueError('Generated model changed: '+name)
    lib = pdk/'libs.ref/sg13cmos5l_stdcell/lib/sg13cmos5l_stdcell_typ_1p20V_25C.lib'
    latch = pdk/'libs.tech/librelane/sg13cmos5l_stdcell/latch_map.v'
    census = json.loads((model/'configuration-cost.json').read_text())
    if tile not in census['tiles']:
        raise ValueError('Tile outside qualified fabric')
    expected_latches = census['tiles'][tile]['stored_bits']
    sources = [model/'library/models_pack.v']
    sources += [model/'library/primitives'/name/'fabulous'/(name+'.v')
                for name in ('FABULOUS_LC','IOBUF','GBUF','SYS_RESET')]
    sources += sorted((model/'library/primitives/WARP/fabulous').glob('*.v'))
    sources += [model/'rtl'/(tile+'.v'),model/'rtl'/(tile+'_switch_matrix.v')]
    if expected_latches:
        sources.append(model/'rtl'/(tile+'_ConfigMem.v'))
    inputs = [manifest,lib,latch,*sources]
    before = {str(p):sha(p) for p in inputs}
    out.mkdir(parents=True,exist_ok=False)
    quote = lambda p: json.dumps(str(p))
    commands = ['read_liberty -lib '+quote(lib),
                'read_verilog -sv '+' '.join(map(quote,sources)),
                'synth -top '+tile+' -flatten',
                'techmap -map '+quote(latch),
                'dfflibmap -liberty '+quote(lib),
                'abc -liberty '+quote(lib), 'clean',
                'write_json '+quote(out/'mapped.json'),
                'tee -o '+quote(out/'stat.json')+' stat -json -liberty '+quote(lib)]
    script = out/'map.ys';script.write_text('\n'.join(commands)+'\n')
    with (out/'yosys.log').open('w') as log:
        subprocess.run(['yosys','-Q','-T','-s',str(script)],stdout=log,stderr=subprocess.STDOUT,
                       check=True,timeout=180)
    netlist = json.loads((out/'mapped.json').read_text())['modules'][tile]
    cells = Counter(cell['type'] for cell in netlist['cells'].values())
    validate_cells(cells, expected_latches)
    if before != {str(p):sha(p) for p in inputs}:
        raise ValueError('Inputs changed during synthesis')
    stat = json.loads((out/'stat.json').read_text())['modules']['\\'+tile]
    result = dict(passed=True,tile=tile,expected_configuration_latches=expected_latches,
                  global_tracks=description['global_tracks'],
                  input_sha256=before,cell_counts=dict(cells),mapped_cell_area_um2=stat.get('area',0),
                  yosys=subprocess.check_output(['yosys','-V'],text=True).strip(),
                  physical_acceptance=False,timing_acceptance=False,equal_area_comparison=False,
                  scope='Regenerated tile synthesis with full configuration latch census; excludes physical buffers, routing, placement and shell. Not physical area.')
    (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result


def run_all(model, pdk, out):
    model,out=Path(model).resolve(),Path(out).resolve()
    census=json.loads((model/'configuration-cost.json').read_text())
    out.mkdir(parents=True,exist_ok=False)
    rows={name:run(model,pdk,out/name,name) for name in sorted(census['tiles'])}
    total=sum(rows[name]['mapped_cell_area_um2']*tile['copies']
              for name,tile in census['tiles'].items())
    latches=sum(rows[name]['expected_configuration_latches']*tile['copies']
                for name,tile in census['tiles'].items())
    if latches != census['totals']['stored_bits']:
        raise ValueError('Whole-grid configuration census changed')
    result=dict(passed=True,tiles=rows,idealized_fabric_cell_area_um2=total,
                configuration_latches=latches,run=os.environ.get('GITHUB_RUN_ID'),
                attempt=os.environ.get('GITHUB_RUN_ATTEMPT'),
                source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                physical_acceptance=False,timing_acceptance=False,equal_area_comparison=False,
                scope='Sum of mapped tile cell areas with actual multiplicities; excludes shell, physical buffers, clock/power/routing/padding. Not whole-chip area or fit.')
    (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('model','pdk','out'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--tile',default='LUT4x8_ha')
    args=parser.parse_args()
    if args.tile == 'all':
        result=run_all(args.model,args.pdk,args.out)
        print(json.dumps({k:v for k,v in result.items() if k!='tiles'},sort_keys=True))
    else:
        print(json.dumps(run(args.model,args.pdk,args.out,args.tile),sort_keys=True))

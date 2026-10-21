"""Generate an oversized software capacity reference, not a physical candidate."""
import argparse
from collections import Counter
import csv
import io
import json
from pathlib import Path
import pickle
import shutil
import subprocess

from qualify_generator import ROOT, compare_control, digest


def expanded_csv(text):
    rows = list(csv.reader(io.StringIO(text)))
    start = next(i for i,r in enumerate(rows) if r and r[0] == 'FabricBegin')
    end = next(i for i,r in enumerate(rows) if r and r[0] == 'FabricEnd')
    grid = rows[start+1:end]
    if len(grid) != 5 or any(len(row) != 6 for row in grid):
        raise ValueError('Expected frozen G1 grid')
    if Counter(t for row in grid for t in row)['LUT4x8_ha'] != 11:
        raise ValueError('Wrong control resource mix')
    lut = 'LUT4x8_ha'
    replacement = [['NW_term', *(['N_IO']*6), 'NE_term'],
                   ['W_IO4', *([lut]*6), 'E_IO4'],
                   ['W_IO4', lut, 'PRIM2T2S', lut, lut, 'PRIM2T2S', lut, 'E_IO4'],
                   ['W_IO4', *([lut]*6), 'E_IO4'],
                   ['SW_term', *(['S_IO2']*6), 'SE_term']]
    out = io.StringIO()
    csv.writer(out, lineterminator='\n').writerows(rows[:start+1]+replacement+rows[end:])
    return out.getvalue()


DIAGNOSTIC_CORNER = 'nom_slow_1p08V_125C'


def placeholder_corner(modeldir, pips):
    """Export the compiler-required filename without claiming characterized delay."""
    (modeldir/f'pips.{DIAGNOSTIC_CORNER}.txt').write_text(pips)
    (modeldir/'timing-unqualified.json').write_text(json.dumps(dict(
        timing_acceptance=False, characterized=False, corner_label=DIAGNOSTIC_CORNER,
        scope='Filename compatibility only; generated placeholder PIP delays. Do not compare rates or Fmax.'),indent=2)+'\n')


def run(control, out, tracks=8, emit_rtl=False):
    from fabulous.fabulous_api import FABulous_API
    from fabulous.fabric_generator.code_generator.code_generator_Verilog import VerilogCodeGenerator
    import yaml
    control, out = Path(control).resolve(), Path(out).resolve()
    check = json.loads((control/'qualification.json').read_text())
    if check['passed'] is not True:
        raise ValueError('Control not qualified')
    compare_control(control, ROOT/'macro/warp_g1/fabulous')
    for name, expected in check['generated_sha256'].items():
        if digest((control/name).read_bytes()) != expected:
            raise ValueError('Changed qualified control output')
    library = control/'library'
    actual = {str(p.relative_to(library)):digest(p.read_bytes()) for p in sorted(library.rglob('*')) if p.is_file()}
    if actual != check['library_sha256']:
        raise ValueError('Changed qualified library')
    if out == control or control in out.parents or out in control.parents:
        raise ValueError('Output and control must be disjoint')
    out.mkdir(parents=True, exist_ok=False)
    proposals = None
    if tracks != 8 or emit_rtl:
        from fold_tracks import transform
        original = FABulous_API(VerilogCodeGenerator())
        original.loadFabric(control/'r1_g1_control.csv')
        copied = out/'library'
        shutil.copytree(library, copied)
        if tracks != 8:
            proposals = transform(copied, original.getTiles(), tracks)
        library = copied
    modeldir = out/'macro/fabulous/.FABulous'
    modeldir.mkdir(parents=True)
    fabric = out/'r1_resource_control.csv'
    fabric.write_text(expanded_csv((control/'r1_g1_control.csv').read_text()).replace(
        str(control/'library'), str(library)))
    api = FABulous_API(VerilogCodeGenerator())
    api.loadFabric(fabric)
    if tracks != 8 or emit_rtl:
        from fabulous.fabric_generator.gen_fabric.gen_configmem import generateConfigMemInit
        for tile in api.getTiles():
            directory = library/'tiles/tiny'/tile.name
            if tile.globalConfigBits:
                config = directory/(tile.name+'_ConfigMem.csv')
                generateConfigMemInit(config, tile.globalConfigBits,
                                      api.fabric.frameBitsPerRow, api.fabric.maxFramesPerCol)
                api.setWriterOutputFile(directory/(tile.name+'_ConfigMem.v'))
                api.genConfigMem(tile.name, config)
            api.setWriterOutputFile(directory/(tile.name+'_switch_matrix.v'))
            api.genSwitchMatrix(tile.name)
            api.setWriterOutputFile(directory/(tile.name+'.v'))
            api.genTile(tile.name)
        from profiling.config_cost import census
        flat = out/'rtl'
        flat.mkdir()
        for tile in api.getTiles():
            for source in (library/'tiles/tiny'/tile.name).glob('*.v'):
                shutil.copyfile(source, flat/source.name)
        cost = census(fabric, flat)
        if tracks == 4 and cost['totals']['stored_bits'] != 10976:
            raise ValueError('Generated storage differs from folded graph projection')
        (out/'configuration-cost.json').write_text(json.dumps(cost, indent=2, sort_keys=True)+'\n')
        # Upstream primitive sources use SystemVerilog; generated tile RTL is Verilog.
        sources = [library/'models_pack.v', *sorted(flat.glob('*.v'))]
        sources += [library/'primitives'/name/'fabulous'/(name+'.v')
                    for name in ('FABULOUS_LC','IOBUF','GBUF','SYS_RESET')]
        sources += sorted((library/'primitives/WARP/fabulous').glob('*.v'))
        command = ['iverilog','-g2012','-tnull']
        for tile in api.getTiles():
            command += ['-s', tile.name]
        elaboration = subprocess.run(command+list(map(str,sources)), capture_output=True,
                                     text=True, timeout=120)
        (out/'rtl-elaboration.txt').write_text(elaboration.stdout+elaboration.stderr)
        if elaboration.returncode:
            raise ValueError('Generated tile hierarchy does not elaborate')
    model = api.gen_routing_model()
    for name,text in zip(('pips.txt','bel.txt','bel.v2.txt','bel.v3.txt','template.pcf'),model):
        (modeldir/name).write_text(text)
    placeholder_corner(modeldir, model[0])
    spec = api.genBitStreamSpec()
    (modeldir.parent/'bitStreamSpec.bin').write_bytes(pickle.dumps(spec))
    # Timing is a placeholder for compatibility only; never qualify Fmax here.
    shutil.copyfile(ROOT/'macro/warp_g1/fabulous/.FABulous/placement_estimate.txt', modeldir/'placement_estimate.txt')
    counts = Counter(line.split(',')[4] for line in model[1].splitlines() if line and not line.startswith('#'))
    expected = {'FABULOUS_LC':128,'wp_timer':4,'wp_shift':4,'IOBUF':42}
    if any(counts[k] != v for k,v in expected.items()):
        raise ValueError('Generated resource census differs')
    pins = list(csv.DictReader((ROOT/'arch/warp_g1/pins.csv').open()))
    for pin in pins:
        if pin['bel'].startswith('X5Y'):
            pin['bel'] = pin['bel'].replace('X5Y','X7Y',1)
    with (out/'pins.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(pins[0]));writer.writeheader();writer.writerows(pins)
    (out/'arch.yaml').write_text(yaml.safe_dump(dict(name='r1_resource_control',arch_version=0x00FE,
        macro=str(out/'macro'),luts=128,primitives=dict(wp_timer=4,wp_shift=4),
        include_border_rows=True,config_rows=5,config_cols=8),sort_keys=False))
    result = dict(passed=True,global_tracks=tracks,track_proposals=proposals,
                  control_qualification_sha256=digest((control/'qualification.json').read_bytes()),
                  resources=dict(counts),source_fabric_sha256=digest(fabric.read_bytes()),
                  generated_sha256={str(p.relative_to(out)):digest(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()},
                  scope='Oversized six-column software capacity control only. Original tile geometry does not establish equal-area fit. No production architecture selected; diagnostic architecture ID0x00FE cannot load on G1.',
                  physical_acceptance=False,timing_acceptance=False,physical_candidate=False,
                  timing_policy='explicit_placeholder_corner_file_not_characterized')
    (out/'resource-control.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--tracks',type=int,choices=(4,8),default=8)
    parser.add_argument('--emit-rtl',action='store_true')
    args=parser.parse_args()
    print(json.dumps(run(args.control,args.out,args.tracks,args.emit_rtl)['resources'],sort_keys=True))

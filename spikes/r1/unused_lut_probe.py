"""One-bit unused-LUT timing sensitivity experiment; never timing acceptance.

The candidate changes only an analysis case value. It is not a loaded bitstream
or a demonstrated functional repair. Original source views and controls survive.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re

from profiling.r1_quiesce import PlainSpec
from compile.bitgen import fasm_features
from run_timing import compare, parse_log

SOURCE_RUN = 40128859740
SOURCE_SHA = '97f655a1e8ed574c553fdc3989154df77fdc314b'
ARTIFACT_ID = 12574475845
ARCHIVE_SHA = 'd3ebcd915e82c6b9646648efe0053e2baf2d790312769beff707bb99e9d0f900'
RUNNER = '/home/runner/work/protocol-emulator-asic/protocol-emulator-asic'
TILE = 'X2Y3'
NATIVE_TILE = 'Tile_X2Y3_LUT4x8_ha'
ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def context(run, artifact):
    expected = dict(id=SOURCE_RUN, head_sha=SOURCE_SHA, head_branch='efpga',
                    path='.github/workflows/r1_run_timing.yaml', run_attempt=1,
                    status='completed', conclusion='failure')
    if any(run.get(k) != v for k, v in expected.items()):
        raise ValueError('Wrong original timing control')
    if (artifact.get('id') != ARTIFACT_ID or artifact.get('expired') is not False
            or artifact.get('name') != f'r1-configured-timing-{SOURCE_RUN}'
            or artifact.get('digest') != 'sha256:' + ARCHIVE_SHA
            or artifact.get('workflow_run', {}).get('id') != SOURCE_RUN
            or artifact.get('workflow_run', {}).get('head_sha') != SOURCE_SHA):
        raise ValueError('Wrong original timing capsule')


def parking_bit(features, spec, module, state):
    """Locate G.FF only if G has no declared use, by actual frame pin wiring."""
    for feature in features:
        tile, source, dest = feature.split('.')
        if tile == TILE and (source == 'G' or source == 'LG_O' or dest == 'LG_O'):
            raise ValueError('The selected LUT is used; parking forbidden')
    bits = spec['TileSpecs'][TILE]['G.FF']
    if len(bits) != 1 or set(bits.values()) != {'1'}:
        raise ValueError('Expected one existing FF select bit')
    index = next(iter(bits))
    if type(index) is not int or not 0 <= index < 640:
        raise ValueError('Invalid frame address')
    frame, offset = divmod(index, 32)
    data = module['ports']['FrameData']['bits'][offset]
    gate = module['ports']['FrameStrobe']['bits'][frame]
    matches = [name for name, c in module['cells'].items()
               if c['type'] == 'sg13cmos5l_dlhq_1'
               and c['connections'].get('D') == [data]
               and c['connections'].get('GATE') == [gate]]
    if len(matches) != 1 or state.get(matches[0]) != '0':
        raise ValueError('Missing unique zero-valued native configuration latch')
    return dict(tile=NATIVE_TILE, cell=matches[0], frame=frame, data_bit=offset,
                tile_bit=index, before='0', after='1', feature='X2Y3.G.FF')


def unused_input_bit(features, spec, module, state, lut='D'):
    """Move only an unrouted input proved irrelevant by the observed LUT truth table."""
    features = set(features)
    if lut not in ('D', 'E'):
        raise ValueError('Unsupported measured LUT input probe')
    if any(f.split('.')[0] == TILE and f.split('.')[2] == f'L{lut}_I1' for f in features):
        raise ValueError('LUT input has a declared route; cannot change it')
    entries = spec['TileSpecs'][TILE]
    init = 0
    for bit in range(16):
        key = f'{lut}.INIT' if bit == 0 else f'{lut}.INIT[{bit}]'
        mapping = entries[key]
        if len(mapping) != 1 or set(mapping.values()) != {'1'}:
            raise ValueError('Unexpected LUT truth-bit encoding')
        index = next(iter(mapping)); frame, offset = divmod(index, 32)
        data = module['ports']['FrameData']['bits'][offset]
        gate = module['ports']['FrameStrobe']['bits'][frame]
        matches = [n for n, c in module['cells'].items() if c['type'] == 'sg13cmos5l_dlhq_1'
                   and c['connections'].get('D') == [data] and c['connections'].get('GATE') == [gate]]
        if len(matches) != 1 or state.get(matches[0]) not in ('0', '1'):
            raise ValueError('Missing observed native truth bit')
        value = int(state[matches[0]])
        declared = f'{TILE}.{key}' in features or (bit == 0 and f'{TILE}.{lut}.INIT[0]' in features)
        if value != declared:
            raise ValueError('Observed LUT truth differs from original FASM')
        init |= value << bit
    if any(((init >> address) & 1) != ((init >> (address ^ 2)) & 1) for address in range(16)):
        raise ValueError('LUT function depends on I1; input reroute forbidden')
    # Reuse strict native-frame localization for the one existing selector bit.
    alternate = 'J2END_CD_END1.LD_I1' if lut == 'D' else 'J_l_EF_END1.LE_I1'
    derived = {'TileSpecs': {TILE: {'G.FF': entries[alternate]}}}
    bit = parking_bit([], derived, module, state)
    bit.update(feature=TILE + '.' + alternate, lut=lut, unused_input=1,
               observed_init=init, cofactor_addresses_checked=16,
               scope='Unrouted I1, observed LUT function independent of I1; analysis only')
    return bit


def registered_h_source(module,select_bit):
    drivers={bit:(name,c) for name,c in module['cells'].items()
             for pin,d in c['port_directions'].items() if d=='output' for bit in c['connections'][pin]}
    _,gate=drivers[module['netnames']['LH_O']['bits'][0]]
    if gate['type']!='sg13cmos5l_a21oi_1' or gate['connections']['A2']!=[select_bit]:
        raise ValueError('Registered H output gate differs')
    _,nor=drivers[gate['connections']['B1'][0]]
    if nor['type']!='sg13cmos5l_nor3_1' or [select_bit] not in list(nor['connections'].values()):
        raise ValueError('Registered H combinational arm is not masked')
    _,inv=drivers[gate['connections']['A1'][0]]
    if inv['type']!='sg13cmos5l_inv_1':raise ValueError('Registered H output inversion differs')
    name,register=drivers[inv['connections']['A'][0]]
    if register['type']!='sg13cmos5l_dfrbpq_1' or register['connections']['Q']!=inv['connections']['A']:
        raise ValueError('Alternate H source does not reach a user flip-flop')
    return name


def unused_upstream_bit(features,spec,module,state,words,pips):
    from selected_route import selected_predecessors,trace_route
    proof=unused_input_bit(features,spec,module,state)
    entries=spec['TileSpecs'][TILE]
    dest='J2MID_CDa_BEG1';alternate='JE2END4.'+dest
    bits=entries[alternate]
    for feature in features:
        tile,source,target=feature.split('.')
        if tile==TILE and (target==dest or set(entries[source+'.'+target]) & set(bits)):
            raise ValueError('Upstream selector overlaps an active feature')
    selected=parking_bit([],{'TileSpecs':{TILE:{'G.FF':bits}}},module,state)
    h=entries['H.FF']
    if len(h)!=1 or set(h.values())!={'1'}:raise ValueError('Unexpected H register encoding')
    index=next(iter(h));frame,offset=divmod(index,32)
    matches=[n for n,c in module['cells'].items() if c['type']=='sg13cmos5l_dlhq_1'
             and c['connections'].get('D')==[module['ports']['FrameData']['bits'][offset]]
             and c['connections'].get('GATE')==[module['ports']['FrameStrobe']['bits'][frame]]]
    if len(matches)!=1 or state.get(matches[0])!='1' or f'{TILE}.H.FF' not in features:
        raise ValueError('Alternate source is not observed registered H')
    user_register=registered_h_source(module,module['cells'][matches[0]]['connections']['Q'][0])
    before=trace_route(selected_predecessors(spec,words,pips),(TILE,'LD_I1'))
    candidate=list(words);index=selected['tile_bit'];frame,offset=divmod(index,32)
    candidate[1+(2*20+frame)*6+1+(4-3)]|=1<<offset
    after=trace_route(selected_predecessors(spec,candidate,pips),(TILE,'LD_I1'))
    if before[-1]!=(TILE,'LD_O') or after[-1]!=(TILE,'LH_O'):
        raise ValueError('Expected feedback-to-registered-source topology not reproduced')
    selected.update(feature=TILE+'.'+alternate,lut='D',unused_input=1,
        observed_init=proof['observed_init'],cofactor_addresses_checked=16,
        source_register_select_latch=matches[0],source_user_register=user_register,route_before=before,route_after=after,
        scope='Unused D I1, one free upstream selector; observed H.FF=1. Analysis only; no image/functional/delay acceptance.')
    return selected


def change_case(text, bit):
    pin = bit['tile'] + '/' + bit['cell'] + '/Q'
    original = (f'set p [get_pins -quiet {{{pin}}}]\n'
                'if {[llength $p]!=1} {error "missing configuration pin"}\n'
                'set_case_analysis 0 $p')
    replacement = original.replace('set_case_analysis 0 ', 'set_case_analysis 1 ', 1)
    guard = f'[get_pins {{{pin}}}] 0]]!="0"'
    changed_guard = guard[:-2] + '1"'
    if text.count(original) != 1 or text.count(guard) != 1:
        raise ValueError('Missing exact original configuration case and guard')
    return text.replace(original, replacement, 1).replace(guard, changed_guard, 1)


def edge_trace():
    lines = ['puts "R1_EDGE_TRACE_BEGIN"']
    for cell, output, pins in [
        ('Tile_X2Y3_LUT4x8_ha/_0775_', 'X', ('A0', 'A1', 'S')),
        ('Tile_X2Y3_LUT4x8_ha/_0776_', 'X', ('A0', 'A1', 'S')),
        ('Tile_X2Y4_S_IO2/_097_', 'X', ('A0', 'A1', 'A2', 'A3', 'S0', 'S1'))]:
        lines += [f'puts "R1_EDGE_TRACE_CELL {cell}"', f'sta::report_constant {{{cell}}}']
        for pin in pins:
            # Pinned OpenSTA2.7 accepts -from/-to here, but not newer -digits.
            lines.append(f'sta::report_edges -from {{{cell}/{pin}}} -to {{{cell}/{output}}}')
    for endpoint in ('Tile_X2Y2_PRIM2T2S/_2158_/D', 'Tile_X2Y3_LUT4x8_ha/_1734_/D'):
        lines += [f'puts "R1_EDGE_TRACE_PATH {endpoint}"',
                  f'report_checks -to [get_pins {{{endpoint}}}] -path_delay max -group_path_count 1 -fields {{slew cap fanout}} -digits 6']
    lines += ['puts "R1_EDGE_TRACE_END"']
    return '\n'.join(lines) + '\n'


def prepare(capsule, out, target='unused-output-register', trace_edges=False):
    capsule, out = Path(capsule).resolve(), Path(out).resolve()
    plan = json.loads((capsule / 'analysis/plan.json').read_text())
    def resolve(name):
        prefix = RUNNER + '/build/r1_timing/'
        if name.startswith(prefix):
            path = capsule / name[len(prefix):]
            if '/pdk/' in name and path.suffix == '.lib':
                path = capsule / 'pinned-pdk' / path.name
            return path
        prefix = RUNNER + '/'
        if name.startswith(prefix):
            return ROOT / name[len(prefix):]
        raise ValueError('Unexpected original runner path')
    inputs = {capsule / 'analysis/plan.json': sha(capsule / 'analysis/plan.json')}
    for name, value in plan['input_sha256'].items():
        path = resolve(name)
        if sha(path) != value:
            raise ValueError('Changed original timing source: ' + str(path))
        inputs[path] = value
    for name, value in plan['rendered_sha256'].items():
        path = capsule / 'analysis' / name
        if sha(path) != value:
            raise ValueError('Changed original timing script')
        inputs[path] = value
    resource = capsule / 'model/resource'
    spec_path = resource / 'macro/fabulous/bitStreamSpec.bin'
    manifest = json.loads((resource / 'resource-control.json').read_text())
    if sha(spec_path) != manifest['generated_sha256']['macro/fabulous/bitStreamSpec.bin']:
        raise ValueError('Changed original configuration specification')
    native_path = capsule / 'support/native.json'
    cases = json.loads((capsule / 'support/cases.json').read_text())
    if sha(native_path) != cases['native_sha256']:
        raise ValueError('Changed native gate representation')
    module = json.loads(native_path.read_text())['modules']['LUT4x8_ha']
    state_path = capsule / 'functional/quiescent/configuration-state.json'
    state = json.loads(state_path.read_text())['tiles'][NATIVE_TILE]['q']
    fasm = capsule / 'model/compile/uart_spi_11/design.fasm'
    spec = PlainSpec(io.BytesIO(spec_path.read_bytes())).load()
    if target not in ('unused-output-register', 'unused-input-select', 'unused-e-input-select', 'unused-d-upstream-select'):
        raise ValueError('Unknown experiment target')
    selector = parking_bit if target == 'unused-output-register' else unused_input_bit
    args = (fasm_features(fasm), spec, module, state)
    if target == 'unused-d-upstream-select':
        from compile.bitfile import BitFile
        image=capsule/'functional/quiescent/quiesced.wbit'
        pips_path=resource/'macro/fabulous/.FABulous/pips.txt'
        if sha(pips_path)!=manifest['generated_sha256']['macro/fabulous/.FABulous/pips.txt']:
            raise ValueError('Changed frozen routing graph')
        inputs[image]=sha(image);inputs[pips_path]=sha(pips_path)
        inputs[Path(__file__).with_name('selected_route.py')]=sha(Path(__file__).with_name('selected_route.py'))
        bit=unused_upstream_bit(*args,BitFile.load(image).words,pips_path.read_text())
        report=capsule/'analysis/static.log';inputs[report]=sha(report)
        register=parse_log(report.read_text())['ffs'].get(NATIVE_TILE+'/'+bit['source_user_register'])
        if register is None or not register['clocked']:
            raise ValueError('Registered alternate is not covered by the original RUN clock')
    else:
        bit = unused_input_bit(*args, lut='E') if target == 'unused-e-input-select' else selector(*args)
    out.mkdir(parents=True, exist_ok=False)
    def relocate(text):
        # Explicit path relocation only; no source/state/connectivity rewrite.
        lib_old = next(n for n in plan['input_sha256'] if n.endswith('.lib'))
        return text.replace(lib_old, str(resolve(lib_old))).replace(
            RUNNER + '/build/r1_timing/', str(capsule) + '/')
    scripts = {}
    for policy in ('static', 'dynamic'):
        source = (capsule / 'analysis' / (policy + '.tcl')).read_text()
        for label, text in [('control', source), ('candidate', change_case(source, bit))]:
            if trace_edges:
                if text.count('puts "RUNSTA_END"') != 1:
                    raise ValueError('Missing unique original report terminator')
                text = text.replace('puts "RUNSTA_END"', edge_trace() + 'puts "RUNSTA_END"')
            name = label + '_' + policy + '.tcl'
            (out / name).write_text(relocate(text))
            scripts[name] = sha(out / name)
    native = json.loads((capsule / 'leaf-audit.json').read_text())['native_exports']
    library = resolve(next(n for n in plan['input_sha256'] if n.endswith('.lib')))
    lines = [f'read_liberty -lib "{library}"']
    for kind, row in sorted(native.items()):
        path = resolve(row['path'])
        if sha(path) != row['sha256']:
            raise ValueError('Native export changed: ' + kind)
        inputs[path] = row['sha256']
        lines.append(f'read_verilog "{path}"')
    lines.append(f'write_json "{out}/all-native.json"')
    (out / 'export.ys').write_text('\n'.join(lines) + '\n')
    scripts['export.ys'] = sha(out / 'export.ys')
    for path in (Path(__file__).resolve(), spec_path, native_path, state_path, fasm,
                 capsule / 'support/cases.json', resource / 'resource-control.json'):
        inputs[path] = sha(path)
    result = dict(source_run=SOURCE_RUN, source_sha=SOURCE_SHA, target=target, change=bit,
                  read_only_edge_trace=trace_edges,
                  input_sha256={str(p): value for p, value in inputs.items()},
                  scripts_sha256=scripts, timing_acceptance=False,
                  loaded_candidate_tested=False, runner_paths_relocated=True)
    (out / 'plan.json').write_text(json.dumps(result, indent=2) + '\n')


def audit(out):
    out = Path(out).resolve()
    plan = json.loads((out / 'plan.json').read_text())
    for path, value in plan['input_sha256'].items():
        if sha(path) != value:
            raise ValueError('Original experiment input changed')
    for name, value in plan['scripts_sha256'].items():
        if sha(out / name) != value:
            raise ValueError('Experiment timing policy changed')
    rows = {}
    for label in ('control', 'candidate'):
        logs = [parse_log((out / (label + '_' + p + '.log')).read_text())
                for p in ('static', 'dynamic')]
        rows[label] = compare(*logs)
    if (len(rows['control']['loop_policy_differences']) != 6
            or abs(rows['control']['worst_slack_ns'] - 1.508933) > 1e-6):
        raise ValueError('Original six-endpoint timing control not reproduced')
    result = dict(diagnostic_complete=True, change=plan['change'], observations=rows,
                  hypothesis_supported=not rows['candidate']['loop_policy_sensitive'],
                  timing_acceptance=False, physical_acceptance=False,
                  loaded_candidate_tested=False, production_hardware_changed=False,
                  scope='One analysis-only existing configuration bit; no delay/hazard, functional, extracted or full-chip qualification.')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'audit'))
    parser.add_argument('--capsule', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--target', choices=('unused-output-register', 'unused-input-select', 'unused-e-input-select', 'unused-d-upstream-select'), default='unused-output-register')
    parser.add_argument('--trace-edges', action='store_true')
    args = parser.parse_args()
    if args.mode == 'prepare':
        prepare(args.capsule, args.out, args.target, args.trace_edges)
    else:
        audit(args.out)

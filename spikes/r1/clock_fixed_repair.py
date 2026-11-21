"""Prove one unused F input separately for the fixed A and D images."""
import argparse
import copy
import io
import json
from pathlib import Path

from assembly_catalog import sha
from compile.bitfile import BitFile
from compile.bitgen import fasm_features
from configuration_audit import audit
from profiling.r1_quiesce import PlainSpec, derive
from sa_functional import prepare as prepare_native, run
from unused_input_sweep import carry_modes, latch, prove_input


def project_state(modules, template, words):
    """Expected configuration from native frame wiring; never an observation."""
    expected = copy.deepcopy(template)
    for tile, row in expected['tiles'].items():
        x, y = map(int, tile.split('_')[1][1:].split('Y'))
        module = modules[row['tile_type']]
        for name in row['q']:
            pins = module['cells'][name]['connections']
            frame = module['ports']['FrameStrobe']['bits'].index(pins['GATE'][0])
            offset = module['ports']['FrameData']['bits'].index(pins['D'][0])
            word = 1 + (x * 20 + frame) * 6 + 1 + (4 - y)
            row['q'][name] = str((words[word] >> offset) & 1)
    return expected


def prepare(capsule, native, trial, current, out):
    capsule, native, trial, current, out = (Path(p).resolve() for p in (capsule, native, trial, current, out))
    parent = current/'sa_functional'
    failed = json.loads((parent/'result.json').read_text())
    if (str(failed['run']) != '44832060001' or failed['passed'] or
            set(failed['cases']) != {'control'} or not failed['cases']['control']['passed'] or
            '123980.00ns' not in (parent/'native.log').read_text()):
        raise ValueError('Require the retained failed fixed-placement native campaign')
    modules_path = native/'registered_native/all-native.json'
    modules = json.loads(modules_path.read_text())['modules']
    observed = json.loads((parent/'reroute/configuration-state.json').read_text())
    observed_image = BitFile.load(parent/'reroute/quiesced.wbit')
    frame = audit(modules, observed, observed_image.words)
    if not frame['passed'] or frame['compared_configuration_bits'] != 8736:
        raise ValueError('Actual parent A configuration audit incomplete')
    prepare_native(capsule, native, trial, out, trial_kind='spi_clock_fixed')
    spec_path = capsule/'model/resource/macro/fabulous/bitStreamSpec.bin'
    spec = PlainSpec(io.BytesIO(spec_path.read_bytes())).load()
    pips_path = capsule/'model/resource/macro/fabulous/.FABulous/pips.txt'
    pips = pips_path.read_text()
    module = modules['LUT4x8_ha']
    proof = dict(parent_run=failed['run'], cases={}, scope='A parent is observed. D parent is projected from its own image; all proof-relevant fields must equal measured A. Future actual native audits remain mandatory.')
    bound = [Path(__file__).resolve(), parent/'result.json', parent/'native.log',
             parent/'reroute/configuration-state.json', parent/'reroute/quiesced.wbit', spec_path, pips_path]
    for stage in ('reroute', 'candidate'):
        case = out/(stage+'-case')
        before = out/(stage+'-parent-expected'); before.mkdir()
        parent_image, _, _ = derive(capsule/'model/resource', case, case/'concurrency.wbit', before)
        image = BitFile.load(parent_image)
        state = project_state(modules, observed, image.words)
        if stage == 'reroute' and (image.words != observed_image.words or state != observed):
            raise ValueError('Reconstructed A parent differs from actual loaded state')
        # D routing and LUT pin permutations can differ. Check the fields
        # actually consumed by the proof instead of transplanting A's edit.
        protected = [('X3Y2', key) for key in spec['TileSpecs']['X3Y2']
                     if key.startswith('F.INIT') or key == 'F.FF']
        protected += [(xy, l+'.I0mux') for xy in spec['TileSpecs']
                      if 'A.I0mux' in spec['TileSpecs'][xy] for l in 'ABCDEFGH']
        for xy, key in protected:
            for address in spec['TileSpecs'][xy][key]:
                name, _ = latch(module, address)
                tile = 'Tile_'+xy+'_LUT4x8_ha'
                if state['tiles'][tile]['q'][name] != observed['tiles'][tile]['q'][name]:
                    raise ValueError('D proof-relevant field differs from measured A')
        change = prove_input('X3Y2', 'F', 1, spec, module, state,
                             fasm_features(case/'design.fasm'), image.words, pips,
                             carry_modes(spec, modules, state))
        if (change['observed_init'] != 0xa000 or
                change['route_before'][-1] != ('X5Y3', 'LA_O') or
                change['route_after'][-1] != ('X3Y3', 'LG_O')):
            raise ValueError('Measured unused F input or alternate route changed')
        raw = BitFile.load(case/'concurrency.wbit'); words = list(raw.words)
        if words[change['word']] >> change['word_bit'] & 1:
            raise ValueError('Raw selector is not zero')
        parent_raw = sha(case/'concurrency.wbit')
        words[change['word']] |= 1 << change['word_bit']
        BitFile(raw.arch_version, words).save(case/'concurrency.wbit')
        feature = 'X3Y2.'+change['route_after'][1][1]+'.LF_I1'
        if spec['TileSpecs']['X3Y2'][feature.split('.', 1)[1]] != {change['tile_bit']: '1'}:
            raise ValueError('Alternate selector encoding differs')
        (case/'design.fasm').write_text((case/'design.fasm').read_text().rstrip()+'\n'+feature+'\n')
        report = json.loads((case/'report.json').read_text())
        report['provenance'] = dict(bitfile_sha256=sha(case/'concurrency.wbit'), parent_raw_image_sha256=parent_raw,
                                    kind='One separately cofactor/carry-proved unused F.I1 selector', changes=[change])
        (case/'report.json').write_text(json.dumps(report, indent=2)+'\n')
        after = out/(stage+'-repaired-expected'); after.mkdir()
        repaired, _, _ = derive(capsule/'model/resource', case, case/'concurrency.wbit', after)
        expected_words = list(image.words); expected_words[change['word']] |= 1 << change['word_bit']
        if BitFile.load(repaired).words != expected_words:
            raise ValueError('Quiescence changes more than the one proved selector')
        expected = copy.deepcopy(state); expected['tiles'][change['tile']]['q'][change['cell']] = '1'
        expected_audit = audit(modules, expected, expected_words)
        if expected_audit['compared_configuration_bits'] != 8736:
            raise ValueError('Expected repaired frame incomplete')
        proof['cases'][stage] = dict(change=change, parent_state_observed=stage == 'reroute',
            expected_states_are_not_observations=True, expected_frame_audit=expected_audit,
            raw_image_sha256=sha(case/'concurrency.wbit'), expected_loaded_image_sha256=sha(repaired))
        bound += [parent_image, repaired]
    proof_path = out/'unused-f-proof.json'
    proof_path.write_text(json.dumps(proof, indent=2)+'\n')
    plan = json.loads((out/'plan.json').read_text())
    bound += [Path(p) for p in plan['input_sha256']]
    bound.append(proof_path)
    plan['input_sha256'] = {str(p): sha(p) for p in bound}
    plan['repair'] = 'One separately proved X3Y2/F.I1 selector per rerouted A and D image'
    (out/'plan.json').write_text(json.dumps(plan, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    p = sub.add_parser('prepare')
    for name in ('capsule', 'native', 'trial', 'current', 'out'):
        p.add_argument('--'+name, type=Path, required=True)
    p = sub.add_parser('run')
    for name in ('out', 'pdk', 'icarus'):
        p.add_argument('--'+name, type=Path, required=True)
    args = vars(parser.parse_args()); mode = args.pop('mode')
    (prepare if mode == 'prepare' else run)(**args)

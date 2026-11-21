"""Remove the measured E.I1 loop after combined F/B/G reload passes."""
import argparse
import copy
import io
import json
from pathlib import Path

from assembly_catalog import sha
from clock_fixed_g_loop_repair import prepare as prepare_first
from run_timing import parse_log
from compile.bitfile import BitFile
from compile.bitgen import fasm_features
from configuration_audit import audit
from profiling.r1_quiesce import PlainSpec, derive
from sa_functional import run
from unused_input_sweep import carry_modes, prove_input


def prepare(capsule, native, trial, current, loaded, later, latest, out):
    capsule, native, trial, current, loaded, later, latest, out = (Path(p).resolve() for p in (capsule, native, trial, current, loaded, later, latest, out))
    parent = latest/'sa_functional'; timing = latest/'r1_loop_timing'
    result = json.loads((parent/'result.json').read_text())
    static = json.loads((timing/'routed_setup_static.execution.json').read_text())
    dynamic = json.loads((timing/'routed_setup_dynamic.execution.json').read_text())
    text = (timing/'routed_setup_static.log').read_text()
    if (str(result['run']) != '44855809222' or not result['passed'] or
            set(result['cases']) != {'control', 'reroute', 'candidate', 'shell'} or
            any(not row['passed'] for row in result['cases'].values()) or
            result['cases']['candidate'] != result['cases']['shell'] or
            static['returncode'] != 0 or not static['completion_marker'] or
            dynamic['returncode'] != -11 or dynamic['completion_marker'] or
            parse_log(text)['structural_loops'] != 1 or
            'Tile_X2Y3_LUT4x8_ha/_0997_/X' not in text):
        raise ValueError('Require actual complete native pass and retained one-loop STA failure')
    image = BitFile.load(parent/'candidate/quiesced.wbit')
    if sha(parent/'candidate/quiesced.wbit') != '02eacca834b2d927aaedb9065faa1c6521ad19a08008c9828b85e4df70449b25':
        raise ValueError('Loaded F/B/G-input repair image changed')
    modules = json.loads((native/'registered_native/all-native.json').read_text())['modules']
    state = json.loads((parent/'candidate/configuration-state.json').read_text())
    frame = audit(modules, state, image.words)
    if not frame['passed'] or frame['compared_configuration_bits'] != 8736:
        raise ValueError('Actual parent frame audit incomplete')
    spec_path = capsule/'model/resource/macro/fabulous/bitStreamSpec.bin'
    spec = PlainSpec(io.BytesIO(spec_path.read_bytes())).load()
    pips_path = capsule/'model/resource/macro/fabulous/.FABulous/pips.txt'
    change = prove_input('X2Y3', 'E', 1, spec, modules['LUT4x8_ha'], state,
                         fasm_features(parent/'candidate-case/design.fasm'), image.words,
                         pips_path.read_text(), carry_modes(spec, modules, state))
    if (change['observed_init'] != 0xaaa0 or
            change['route_before'][-1] != ('X1Y3', 'LC_O') or
            change['route_after'][-1] != ('X2Y4', 'B_OUT')):
        raise ValueError('Measured E feedback or alternate input route changed')
    prepare_first(capsule, native, trial, current, loaded, later, out)
    case = out/'candidate-case'
    if sha(case/'concurrency.wbit') != sha(parent/'candidate-case/concurrency.wbit'):
        raise ValueError('Reconstructed F/B/G repair differs from actual loaded parent')
    raw = BitFile.load(case/'concurrency.wbit'); words = list(raw.words)
    if words[change['word']] >> change['word_bit'] & 1:
        raise ValueError('Raw selector is not zero')
    words[change['word']] |= 1 << change['word_bit']
    BitFile(raw.arch_version, words).save(case/'concurrency.wbit')
    feature = 'X2Y3.'+change['route_after'][1][1]+'.LE_I1'
    if spec['TileSpecs']['X2Y3'][feature.split('.', 1)[1]] != {change['tile_bit']: '1'}:
        raise ValueError('Alternate selector encoding differs')
    (case/'design.fasm').write_text((case/'design.fasm').read_text().rstrip()+'\n'+feature+'\n')
    report = json.loads((case/'report.json').read_text())
    report['provenance']['bitfile_sha256'] = sha(case/'concurrency.wbit')
    report['provenance']['changes'].append(change)
    report['provenance']['kind'] = 'Separate unused F.I1, B.I3, G.I2 and E.I1 selector proofs'
    (case/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    expected_dir = out/'e-loop-repaired-expected'; expected_dir.mkdir()
    repaired, _, _ = derive(capsule/'model/resource', case, case/'concurrency.wbit', expected_dir)
    expected_words = list(image.words); expected_words[change['word']] |= 1 << change['word_bit']
    if BitFile.load(repaired).words != expected_words:
        raise ValueError('Additional quiescence changes beyond one selector')
    expected = copy.deepcopy(state); expected['tiles'][change['tile']]['q'][change['cell']] = '1'
    frame = audit(modules, expected, expected_words)
    if frame['compared_configuration_bits'] != 8736:
        raise ValueError('Expected frame audit incomplete')
    proof = out/'e-loop-proof.json'
    proof.write_text(json.dumps(dict(parent_native_run=result['run'], change=change,
        expected_states_are_not_observations=True, expected_frame_audit=frame,
        raw_image_sha256=sha(case/'concurrency.wbit'), expected_loaded_image_sha256=sha(repaired)), indent=2)+'\n')
    plan = json.loads((out/'plan.json').read_text())
    bound = [Path(p) for p in plan['input_sha256']]
    bound += [Path(__file__).resolve(), parent/'result.json', parent/'candidate/configuration-state.json',
              parent/'candidate/quiesced.wbit', parent/'candidate-case/design.fasm', spec_path, pips_path,
              timing/'routed_setup_static.execution.json', timing/'routed_setup_dynamic.execution.json',
              timing/'routed_setup_static.log', proof, repaired]
    plan['input_sha256'] = {str(p): sha(p) for p in bound}
    plan['repair'] += '; candidate only: proved-unused X2Y3/E.I1 cyclic route'
    (out/'plan.json').write_text(json.dumps(plan, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    p = sub.add_parser('prepare')
    for name in ('capsule', 'native', 'trial', 'current', 'loaded', 'later', 'latest', 'out'):
        p.add_argument('--'+name, type=Path, required=True)
    p = sub.add_parser('run')
    for name in ('out', 'pdk', 'icarus'):
        p.add_argument('--'+name, type=Path, required=True)
    args = vars(parser.parse_args()); mode = args.pop('mode')
    (prepare if mode == 'prepare' else run)(**args)

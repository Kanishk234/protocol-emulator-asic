#!/usr/bin/env python3
"""Prepare and prove one isolated R4 RTL trial. Run in the project venv.

Example: python scripts/ci/verify_timing_trial.py bs-resync /tmp/bs-resync-proof
Raw proof/simulation output stays in the explicitly selected new directory.
"""
import argparse
import io
import importlib.util
from pathlib import Path
import subprocess
import tarfile

from timing_trial import CANDIDATE, PATCHES

ROOT = Path(__file__).resolve().parents[2]


def regenerate_python_tables(output):
    """Use trial resource counts without rewriting its archived RTL."""
    import yaml
    generator_spec = importlib.util.spec_from_file_location('trial_generator', output / 'tools/gen/gen.py')
    generator = importlib.util.module_from_spec(generator_spec)
    generator_spec.loader.exec_module(generator)
    spec = yaml.safe_load((output / 'spec/tripwire.yaml').read_text())
    generator.validate(spec)
    (output / 'tools/tripwire_spec.py').write_text(generator.gen_python(spec))


def verify(variant, output, simulate=False):
    patch, source = PATCHES[variant]
    output = output.resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError("Trial output must be outside the repository")
    output.mkdir(parents=True, exist_ok=False)
    for revision, paths in [(CANDIDATE, ['src', 'spec', 'programs']),
                            ('HEAD', ['tools', 'test_internal'])]:
        data = subprocess.check_output(['git', 'archive', revision, *paths], cwd=ROOT)
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            archive.extractall(output, filter='data')
    # HEAD supplies current test/model fixes, but its generated tables describe
    # main's resource counts. Regenerate only Python encodings from frozen spec.
    regenerate_python_tables(output)
    original = (output / source).read_text()
    subprocess.run(['git', 'apply', str(ROOT / 'spikes/r4_floorplan' / patch)],
                   cwd=output, check=True)
    module = Path(source).stem
    gold = output / f'gold_{module}.v'
    gold.write_text(original)
    for count in ([1, 5, 6, 7, 9, 16] if module == 'trw_chan_port' else [None]):
        param = f'chparam -set N {count} {module}\n' if count else ''
        tag = f'equiv-n{count}' if count else 'equiv'
        # Relative include paths avoid Yosys treating quotes in -I as literal text.
        script = (f'read_verilog -DSYNTHESIS -Isrc gold_{module}.v\n'
                  f'{param}rename {module} gold\n'
                  f'read_verilog -DSYNTHESIS -Isrc {source}\n'
                  f'{param}rename {module} gate\n'
                  'proc\nmemory\nopt\nequiv_make gold gate equiv\nhierarchy -top equiv\n'
                  'equiv_simple\nequiv_induct -seq 2\nequiv_status -assert\n')
        script_path = output / f'{tag}.ys'
        script_path.write_text(script)
        with (output / f'{tag}.log').open('w') as log:
            subprocess.run(['yosys', '-Q', '-s', str(script_path)], stdout=log,
                           stderr=subprocess.STDOUT, check=True, timeout=180, cwd=output)
        print(f'{variant}: {tag} passed', flush=True)
    if simulate:
        suites = [('chan', [])] if module == 'trw_chan_port' else [('pin', [
            'FULL=1', 'COCOTB_TEST_MODULES=test_pin_bs,test_pin_bs_frame,test_pin_bs_tx,test_pin_bs_b3'])]
        suites += [('chip', []), ('l2', [f'RTL_DIR={output / "src"}',
                                      f'RTL_REV={CANDIDATE}-{variant}', 'L2_CYCLES=2048'])]
        for suite, args in suites:
            with (output / f'{suite}.log').open('w') as log:
                subprocess.run(['make', '-C', str(output / 'test_internal' / suite),
                                'SIM=icarus', *args], stdout=log,
                               stderr=subprocess.STDOUT, check=True)
            print(f'{variant}: {suite} passed', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('variant', choices=PATCHES)
    parser.add_argument('output', type=Path)
    parser.add_argument('--simulate', action='store_true')
    args = parser.parse_args()
    verify(args.variant, args.output, args.simulate)

"""Reconstruct and check the isolated low-eight-bit configuration delta cache.

Requires the project venv, Icarus and Yosys. This proves functional properties;
it does not qualify a physical design or authorize detailed routing.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess

from verify_drop_parallel import verify as prepare_counter
from verify_lane_read_mask import digest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / 'fixtures/sample_delta_low8'


def run(output, name, args, *, reject=False):
    with (output / (name + '.log')).open('w') as log:
        result = subprocess.run(args, cwd=output, stdout=log,
                                stderr=subprocess.STDOUT, timeout=180)
    text = (output / (name + '.log')).read_text()
    if reject:
        if result.returncode == 0 or 'Configuration staging changes observable phase behavior' not in text:
            raise ValueError('Negative control did not reject the intended phase error')
    elif result.returncode:
        raise ValueError(f'{name} failed; inspect its log')
    return text


def check_prepared(output):
    """Apply only to the exact counter baseline; compare every source-file hash."""
    output = Path(output).resolve()
    hashes = json.loads((FIXTURE / 'source_hashes.json').read_text())
    before = {p.name: digest(p) for p in (output / 'src').iterdir() if p.is_file()}
    if any(before.get(f) != h['before'] for f, h in hashes.items()):
        raise ValueError('Wrong configuration-cache baseline')
    (output / 'gold.v').write_text((output / 'src/trw_pin_cfg.v').read_text().replace(
        'module trw_pin_cfg', 'module trw_pin_cfg_gold', 1))
    (output / 'bs_original.v').write_bytes((output / 'src/trw_pin_bs.v').read_bytes())
    subprocess.run(['git', 'apply', str(ROOT / 'spikes/r4_floorplan/sample_delta_low8.patch')],
                   cwd=output, check=True)
    after = {p.name: digest(p) for p in (output / 'src').iterdir() if p.is_file()}
    if after != {**before, **{f: h['after'] for f, h in hashes.items()}}:
        raise ValueError('Unexpected configuration-cache source changes')
    for p in FIXTURE.glob('*.v'):
        shutil.copyfile(p, output / p.name)
    gate = (output / 'src/trw_pin_cfg.v').read_text().replace(
        'module trw_pin_cfg', 'module trw_pin_cfg_gate', 1)
    (output / 'gate.v').write_text(gate)
    (output / 'host_blacklist.txt').write_text('')
    proofs = []
    for full in (0, 1):
        for flops in (False, True):
            name = f'cache-{full}-' + ('flops' if flops else 'latches')
            defines = ['-DTRW_PIN_CFG_FLOPS'] if flops else []
            run(output, name + '-compile', ['iverilog', '-g2005', '-Isrc', *defines,
                '-s', 'tb_cfg_staging', f'-Ptb_cfg_staging.FULL={full}',
                '-o', name + '.vvp', 'gold.v', 'gate.v', 'tb_delta_reset_phase.v'])
            phase = run(output, name + '-phase', ['vvp', name + '.vvp'])
            script = f'''read_verilog -nosynthesis -Isrc {' '.join(defines)} gold.v wrapper_gold_{full}.v gate.v wrapper_gate_{full}.v
hierarchy -check
proc
flatten wrapper_gold wrapper_gate
opt
equiv_make -blacklist host_blacklist.txt wrapper_gold wrapper_gate equiv
hierarchy -top equiv
clk2fflogic
opt_clean
equiv_simple
equiv_induct -seq 6
equiv_status -assert
'''
            (output / (name + '.ys')).write_text(script)
            log = run(output, name, ['yosys', '-Q', '-s', name + '.ys'])
            match = re.search(r'Of those cells (\d+) are proven and 0 are unproven', log)
            if not match or 'Equivalence successfully proven!' not in log:
                raise ValueError('Incomplete configuration-cache proof')
            proofs.append(dict(full=full, flops=flops, points=int(match[1]), phase=phase.strip()))
    for name, old, new in (
        ('wrong-reset', "rst_n ? wdata : 16'd0", 'wdata'),
        ('wrong-borrow', 'delta_q[8]};', "1'b0};"),
    ):
        if gate.count(old) != 1:
            raise ValueError('Negative-control source drift')
        (output / (name + '.v')).write_text(gate.replace(old, new))
        run(output, name + '-compile', ['iverilog', '-g2005', '-Isrc', '-s', 'tb_cfg_staging',
            '-Ptb_cfg_staging.FULL=1', '-o', name + '.vvp', 'gold.v', name + '.v', 'tb_delta_reset_phase.v'])
        run(output, name, ['vvp', name + '.vvp'], reject=True)
    script = '''read_verilog -DSYNTHESIS -Isrc bs_original.v bs_gold.v
hierarchy -top wrapper_gold
proc
flatten
memory
opt
design -stash gold
read_verilog -DSYNTHESIS -Isrc src/trw_pin_bs.v bs_gate.v
hierarchy -top wrapper_gate
proc
flatten
memory
opt
design -stash gate
design -copy-from gold -as gold wrapper_gold
design -copy-from gate -as gate wrapper_gate
equiv_make gold gate equiv
hierarchy -top equiv
equiv_simple
equiv_induct -seq 2
equiv_status -assert
'''
    (output / 'bs_consumer.ys').write_text(script)
    log = run(output, 'bs_consumer', ['yosys', '-Q', '-s', 'bs_consumer.ys'])
    if 'Equivalence successfully proven!' not in log:
        raise ValueError('Incomplete bit-time consumer proof')
    receipt = dict(source_hashes=after, configuration_proofs=proofs,
                   consumer_equivalence=True, negative_controls=['reset', 'borrow'],
                   additional_full_unit_state=dict(flops=9, latches=9, clock_gates=1),
                   physical_timing_proven=False, qualified=False)
    (output / 'sample_delta_low8_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def verify(output):
    prepare_counter(output)
    return check_prepared(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.output), indent=2))

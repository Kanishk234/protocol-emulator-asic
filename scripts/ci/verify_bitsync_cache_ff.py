"""Check an isolated bitsync cache FF trial against the prepared closure RTL."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

from verify_cfg_staging import wrapper

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(reference, output):
    reference, output = Path(reference).resolve(), Path(output).resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError('Use an experiment directory outside the repository')
    evidence = ROOT / 'spikes/phase2_stock_flow/bitsync_cache_ff'
    identity = json.loads((evidence / 'identity.json').read_text())
    if (sha(reference / 'src/trw_pin_cfg.v') != identity['reference_sha256']
            or sha(evidence / 'storage.patch') != identity['patch_sha256']):
        raise ValueError('Unexpected experiment source or patch')
    output.mkdir(exist_ok=False, parents=True)
    shutil.copytree(reference / 'src', output / 'src')
    (output / 'gold.v').write_text((output / 'src/trw_pin_cfg.v').read_text().replace(
        'module trw_pin_cfg #(', 'module trw_pin_cfg_gold #(', 1))
    subprocess.run(['git', 'apply', str(evidence / 'storage.patch')], cwd=output, check=True)
    if sha(output / 'src/trw_pin_cfg.v') != identity['candidate_sha256']:
        raise ValueError('Unexpected experiment output')
    (output / 'gate.v').write_text((output / 'src/trw_pin_cfg.v').read_text().replace(
        'module trw_pin_cfg #(', 'module trw_pin_cfg_gate #(', 1))
    return identity


def verify(output, yosys, iverilog='iverilog', vvp='vvp'):
    results = []
    for full in (0, 1):
        exe = output / f'phase{full}.vvp'
        subprocess.run([iverilog, '-g2005', '-Isrc', '-s', 'tb_mode_ff',
            f'-Ptb_mode_ff.FULL={full}', '-o', str(exe), 'gold.v', 'gate.v',
            str(ROOT / 'spikes/phase2_stock_flow/bitsync_cache_ff/tb_cache_ff.v')], cwd=output, check=True)
        log = subprocess.check_output([vvp, str(exe)], cwd=output, text=True, timeout=90)
        (output / f'phase{full}.log').write_text(log)
        if f'PASS full={full} cycles=133152 phase_checks=665770' not in log:
            raise ValueError('Missing complete phase comparison')
        for kind in ('gold', 'gate'):
            text = wrapper(kind, full).replace('output wire carrier_active, restart);',
                'output wire carrier_active, restart, bitsync_active, output wire [24:0] sample_delta);')
            text = text.replace('.carrier_active(carrier_active),.restart(restart));',
                '.carrier_active(carrier_active),.restart(restart),.bitsync_active(bitsync_active),.sample_delta(sample_delta));')
            (output / f'wrapper_{kind}.v').write_text(text)
        script = output / f'proof{full}.ys'
        script.write_text('''read_verilog -nosynthesis -Isrc gold.v gate.v wrapper_gold.v wrapper_gate.v
hierarchy -check
proc
flatten wrapper_gold wrapper_gate
opt
equiv_make wrapper_gold wrapper_gate equiv
hierarchy -top equiv
clk2fflogic
opt_clean
equiv_simple
equiv_induct -seq 6
equiv_status -assert
''')
        with (output / f'proof{full}.log').open('w') as log_file:
            subprocess.run([yosys, '-Q', '-s', str(script)], cwd=output,
                stdout=log_file, stderr=subprocess.STDOUT, check=True, timeout=180)
        proof = (output / f'proof{full}.log').read_text()
        points = re.search(r'Of those cells (\d+) are proven and 0 are unproven', proof)
        if not points or 'Equivalence successfully proven!' not in proof:
            raise ValueError('Missing complete equivalence receipt')
        results.append(dict(full=full, phase_checks=665770,
                            equivalence_points=int(points[1]), induction_sequence_cap=6))
    original = (output / 'gate.v').read_text()
    anchor = "if (mode_write) mode_q <= rst_n ? mode_value : 1'b0;"
    if original.count(anchor) != 1:
        raise ValueError('Ambiguous mutation anchor')
    (output / 'mutant.v').write_text(original.replace(anchor,
        "if (!rst_n) mode_q <= 1'b0; else if (mode_write) mode_q <= mode_value;"))
    exe = output / 'wrong_reset.vvp'
    subprocess.run([iverilog, '-g2005', '-Isrc', '-s', 'tb_mode_ff',
        '-Ptb_mode_ff.FULL=1', '-o', str(exe), 'gold.v', 'mutant.v',
        str(ROOT / 'spikes/phase2_stock_flow/bitsync_cache_ff/tb_cache_ff.v')], cwd=output, check=True)
    mutant = subprocess.run([vvp, str(exe)], cwd=output, text=True,
                            capture_output=True, timeout=90)
    (output / 'wrong_reset.log').write_text(mutant.stdout + mutant.stderr)
    if not mutant.returncode or 'Configuration staging changes observable phase behavior' not in mutant.stdout:
        raise ValueError('Wrong-reset fault was not detected by comparison')
    return dict(checks=results, wrong_reset_mutant_rejected=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--yosys', default='yosys')
    parser.add_argument('--iverilog', default='iverilog')
    parser.add_argument('--vvp', default='vvp')
    args = parser.parse_args()
    identity = prepare(args.reference, args.output)
    result = dict(identity=identity, checks=verify(args.output.resolve(), args.yosys, args.iverilog, args.vvp),
        scope='Configuration module with clocked host writes; no physical qualification')
    (args.output / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))

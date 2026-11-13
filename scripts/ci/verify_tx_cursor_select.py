"""Reproduce lean/full TX equivalence and an arithmetic negative control."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

from apply_tx_cursor_select import apply

ROOT = Path(__file__).resolve().parents[2]


def verify(reference, output):
    reference, output = Path(reference).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    shutil.copytree(reference, output / 'src')
    gold = (reference / 'trw_pin_tx.v').read_text()
    receipt = apply(output, ROOT / 'spikes/phase2_stock_flow/tx_cursor_select')
    candidate = (output / 'src/trw_pin_tx.v').read_text()
    for kind, text in [('gold', gold), ('gate', candidate)]:
        (output / f'{kind}.v').write_text(text.replace(
            'module trw_pin_tx #(', f'module trw_pin_tx_{kind} #(', 1))
    results = []
    for full in (0, 1):
        script = f'''read_verilog -Isrc gold.v gate.v
chparam -set FULL {full} trw_pin_tx_gold
chparam -set FULL {full} trw_pin_tx_gate
proc
opt
equiv_make trw_pin_tx_gold trw_pin_tx_gate equiv
hierarchy -top equiv
equiv_simple
equiv_induct -seq 6
equiv_status -assert
'''
        (output / f'proof{full}.ys').write_text(script)
        run = subprocess.run(['yosys', '-Q', '-T', '-s', f'proof{full}.ys'],
                             cwd=output, capture_output=True, text=True, timeout=180)
        log = run.stdout + run.stderr
        (output / f'proof{full}.log').write_text(log)
        run.check_returncode()
        match = re.search(r'Of those cells (\d+) are proven and 0 are unproven', log)
        if not match or 'Equivalence successfully proven!' not in log:
            raise ValueError('Missing affirmative TX equivalence evidence')
        results.append(dict(full=full, frac=8, equivalence_points=int(match[1]),
                            induction_sequence_cap=6))
    gate = (output / 'gate.v').read_text()
    if gate.count("17'h1ffff - {5'd0, h_d}") != 1:
        raise ValueError('Missing negative-control mutation site')
    (output / 'mutant.v').write_text(gate.replace("17'h1ffff - {5'd0, h_d}",
                                                "17'h1fffe - {5'd0, h_d}"))
    (output / 'negative.ys').write_text(script.replace('gold.v gate.v', 'gold.v mutant.v'))
    run = subprocess.run(['yosys', '-Q', '-T', '-s', 'negative.ys'], cwd=output,
                         capture_output=True, text=True, timeout=180)
    log = run.stdout + run.stderr
    (output / 'negative.log').write_text(log)
    if not run.returncode or 'unproven $equiv cells' not in log:
        raise ValueError('Arithmetic negative control was not rejected')
    result = dict(source_application=receipt, proofs=results,
                  arithmetic_negative_control_rejected=True,
                  yosys=subprocess.check_output(['yosys', '-V'], text=True).strip(),
                  verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  scope='TX module equivalence at FRAC=8, FULL=0/1; not full-chip formal or physical qualification')
    (output / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.reference, args.output), indent=2))

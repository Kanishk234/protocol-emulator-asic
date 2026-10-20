#!/usr/bin/env python3
"""Verify the isolated banked configuration trial; raw evidence stays outside Git."""
import argparse
import hashlib
import io
import json
import re
import subprocess
import tarfile
from pathlib import Path

from timing_trial import CANDIDATE, PATCHES
from verify_timing_trial import regenerate_python_tables

ROOT = Path(__file__).resolve().parents[2]
VARIANT = 'bs-event-cfg-staging'
VARIANTS = (VARIANT, 'bs-resync-event-cfg-staging')


def proof_script(flops):
    define = '-DTRW_PIN_CFG_FLOPS ' if flops else ''
    return f'''read_verilog -nosynthesis {define}-Isrc gold.v wrapper_gold.v gate.v wrapper_gate.v
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


def wrapper(kind, full):
    # trw_spi registers the write pulse/address/data on this same clock; trw_host
    # decodes those registers combinationally. Do not replace this with unconstrained
    # asynchronous writes or assume carrier outputs are irrelevant.
    return f'''`default_nettype none
`include "trw_defs.vh"
module wrapper_{kind}(input wire clk, rst_n, host_we,
 input wire [4:0] host_addr, input wire [15:0] host_data,
 output wire [`TRW_PC_BITS-1:0] cfg, output wire carrier_active, restart);
 reg we; reg [4:0] waddr; reg [15:0] wdata;
 always @(posedge clk) begin we <= host_we; waddr <= host_addr; wdata <= host_data; end
 trw_pin_cfg_{kind} #(.FULL({full})) u_cfg (.clk(clk),.rst_n(rst_n),.we(we),.waddr(waddr),.wdata(wdata),
 .cfg(cfg),.carrier_active(carrier_active),.restart(restart));
endmodule
'''


def verify_phases(output):
    output = Path(output)
    bench = ROOT / 'test_internal/cfg_staging/tb_cfg_staging.v'
    for kind, source in [('gold', output / 'gold_trw_pin_cfg.v'), ('gate', output / 'src/trw_pin_cfg.v')]:
        (output / f'{kind}.v').write_text(source.read_text().replace(
            'module trw_pin_cfg #(', f'module trw_pin_cfg_{kind} #(', 1))
    # Internal staging intentionally holds on idle cycles. Exclude only its
    # correspondence and its internal combinational predicate; retain cfg,
    # carrier_active, restart, every storage latch and host register proof point.
    (output / 'host_blacklist.txt').write_text(
        'u_cfg.wdata_q\nu_cfg.g_carrier_active.carrier_active_next\n')
    results = []
    for full in (0, 1):
        for flops in (False, True):
            tag = f'full{full}-' + ('flops' if flops else 'latches')
            args = ['iverilog', '-g2005', '-Isrc', '-s', 'tb_cfg_staging',
                    f'-Ptb_cfg_staging.FULL={full}', '-o', tag + '.vvp']
            if flops:
                args += ['-DTRW_PIN_CFG_FLOPS']
            subprocess.run([*args, 'gold.v', 'gate.v', str(bench)], cwd=output, check=True, timeout=30)
            result = subprocess.check_output(['vvp', tag + '.vvp'], cwd=output, text=True, timeout=30)
            (output / (tag + '.log')).write_text(result)
            if f'PASS full={full} cycles=2080 phase_checks=10400' not in result:
                raise ValueError('Missing complete phase comparison receipt')
            for kind in ('gold', 'gate'):
                (output / f'wrapper_{kind}.v').write_text(wrapper(kind, full))
            script = output / (tag + '.ys')
            script.write_text(proof_script(flops))
            with (output / (tag + '-proof.log')).open('w') as log:
                subprocess.run(['yosys', '-Q', '-s', str(script)], cwd=output,
                               stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
            log = (output / (tag + '-proof.log')).read_text()
            match = re.search(r'Of those cells (\d+) are proven and 0 are unproven', log)
            if not match or 'Equivalence successfully proven!' not in log:
                raise ValueError('Missing complete equivalence proof receipt')
            results.append(dict(full=full, flops=flops, phase_checks=10400,
                                equivalence_points=int(match.group(1))))
            print(tag, results[-1], flush=True)
    return results


def prepare(output, variant=VARIANT):
    if variant not in VARIANTS:
        raise ValueError('Unreviewed configuration staging variant')
    output = Path(output).resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError('Use a fresh output directory outside the repository')
    output.mkdir(parents=True, exist_ok=False)
    for revision, paths in [(CANDIDATE, ['src', 'spec']), ('HEAD', ['tools', 'test_internal', 'programs'])]:
        data = subprocess.check_output(['git', 'archive', revision, *paths], cwd=ROOT)
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            archive.extractall(output, filter='data')
    regenerate_python_tables(output)
    source = output / 'src/trw_pin_cfg.v'
    (output / 'gold_trw_pin_cfg.v').write_bytes(source.read_bytes())
    (output / 'gold_trw_pin_bs.v').write_bytes((output / 'src/trw_pin_bs.v').read_bytes())
    patch = ROOT / 'spikes/r4_floorplan' / PATCHES[variant][0]
    subprocess.run(['git', 'apply', str(patch)], cwd=output, check=True)
    return output


def verify_bs(output):
    script = output / 'bs-equivalence.ys'
    script.write_text('''read_verilog -DSYNTHESIS -Isrc gold_trw_pin_bs.v
rename trw_pin_bs gold
read_verilog -DSYNTHESIS -Isrc src/trw_pin_bs.v
rename trw_pin_bs gate
proc
memory
opt
equiv_make gold gate equiv
hierarchy -top equiv
equiv_simple
equiv_induct -seq 2
equiv_status -assert
''')
    log_path = output / 'bs-equivalence.log'
    with log_path.open('w') as log:
        subprocess.run(['yosys', '-Q', '-s', str(script)], cwd=output,
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
    match = re.search(r'Of those cells (\d+) are proven and 0 are unproven', log_path.read_text())
    if not match:
        raise ValueError('Missing complete bit-clock proof receipt')
    return int(match.group(1))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--variant', choices=VARIANTS, default=VARIANT)
    args = parser.parse_args()
    output = prepare(args.output, args.variant)
    bs_points = verify_bs(output)
    results = verify_phases(output)
    receipt = dict(candidate=CANDIDATE, variant=args.variant, checks=results,
                   proof_scope='Sequential module equivalence with clocked host writes; induction cap6, not whole-chip formal',
                   bit_clock_equivalence_points=bs_points,
                   phase_bench_sha256=hashlib.sha256((ROOT / 'test_internal/cfg_staging/tb_cfg_staging.v').read_bytes()).hexdigest(),
                   rtl_sha256={name: hashlib.sha256((output / 'src' / name).read_bytes()).hexdigest()
                               for name in ('trw_pin_cfg.v', 'trw_pin_bs.v')})
    (output / 'cfg_staging_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')


if __name__ == '__main__':
    main()

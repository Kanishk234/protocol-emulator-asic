"""Prove the actual lane action-selection replacement using pinned PDK gates."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-src', type=Path, required=True)
    parser.add_argument('--trial-lane', type=Path, required=True)
    parser.add_argument('--primitive', type=Path, required=True)
    parser.add_argument('--pdk-cells', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    src = args.reference_src.resolve()
    reference = (src / 'trw_lane.v').read_text()
    trial = args.trial_lane.read_text()
    def split(text, declaration):
        start = text.index(declaration)
        end = text.index('    wire [3:0] s_op', start)
        return text[:start], text[start:end], text[end:]
    before, original, after = split(reference, '    reg [SB-1:0] ss;')
    before_trial, replacement, after_trial = split(trial, '    wire [SB-1:0] ss;')
    if before != before_trial or after != after_trial:
        raise ValueError('Trial changed source outside the reviewed selector block')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / 'trw_defs.vh').write_bytes((src / 'trw_defs.vh').read_bytes())
    miter = '''`default_nettype none
`include "trw_defs.vh"
module proof(input wire [11:0] onehot,
input wire [12*`TRW_SLOT_BITS-1:0] slots,output wire equal);
localparam SB=`TRW_SLOT_BITS;
'''
    miter += re.sub(r'\bss\b', 'expected', original)
    miter += re.sub(r'\bss\b', 'actual', replacement)
    miter += '''assign equal=(expected[SB-1:`TRW_SLOT_OP_LSB]
                       ==actual[SB-1:`TRW_SLOT_OP_LSB]);
endmodule
'''
    (output / 'miter.v').write_text(miter)
    pdk = args.pdk_cells.read_text()
    models = []
    for name in ['sg13cmos5l_buf_2', 'sg13cmos5l_a22oi_1', 'sg13cmos5l_antennanp']:
        matches = re.findall(r'(?m)^module ' + name + r'\b.*?endmodule', pdk, re.S)
        if len(matches) != 1:
            raise ValueError('Missing unique PDK model: ' + name)
        models.append(matches[0])
    # The diode is passive and has no functional output in the actual PDK model.
    if re.search(r'\b(output|inout)\b', models[-1]):
        raise ValueError('Diode model is not passive')
    (output / 'pdk_models.v').write_text('\n'.join(models))
    files = [output / 'pdk_models.v', args.primitive.resolve(), output / 'miter.v']
    script = ('read_verilog -DSYNTHESIS '
              + ' '.join(json.dumps(str(p)) for p in files)
              + '; prep -top proof -flatten; delete t:sg13cmos5l_antennanp; '
              + 'sat -verify -prove equal 1')
    result = subprocess.run(['yosys', '-Q', '-T', '-p', script], cwd=output,
                            text=True, capture_output=True)
    (output / 'proof.log').write_text(result.stdout + result.stderr)
    if result.returncode or 'SUCCESS!' not in result.stdout:
        raise ValueError('Actual guarded action-selector proof failed; see proof.log')
    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()
    receipt = dict(scope='Actual action fields only, arbitrary masks/data, PDK gate functions; '
                         'no physical preservation or full-chip sequential proof',
                   passed=True, passive_diodes_omitted_from_sat=True,
                   reference_lane_sha256=sha(src / 'trw_lane.v'),
                   trial_lane_sha256=sha(args.trial_lane),
                   primitive_sha256=sha(args.primitive), pdk_cells_sha256=sha(args.pdk_cells),
                   defines_sha256=sha(src / 'trw_defs.vh'),
                   miter_sha256=sha(output / 'miter.v'), log_sha256=sha(output / 'proof.log'))
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()

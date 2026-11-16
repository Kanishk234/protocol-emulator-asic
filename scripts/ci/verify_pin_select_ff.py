"""Prove a one-word storage follow-up against the existing cache-FF candidate."""
import argparse
import json
from pathlib import Path

from verify_bitsync_cache_ff import ROOT, prepare, verify


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--yosys', default='yosys')
    parser.add_argument('--iverilog', default='iverilog')
    parser.add_argument('--vvp', default='vvp')
    args = parser.parse_args()
    evidence = ROOT / 'spikes/phase2_stock_flow/pin_select_word_ff'
    identity = prepare(args.reference, args.output, evidence)
    result = verify(args.output.resolve(), args.yosys, args.iverilog, args.vvp,
        bench=evidence / 'tb_select_ff.v', phase_checks=665780,
        mutation=("if (dec) q <= rst_n ? wdata[b] : 1'b0;",
                  "if (!rst_n) q <= 1'b0; else if (dec) q <= wdata[b];"))
    receipt = dict(identity=identity, verification=result,
        scope='Configuration module/all outputs under registered host writes; not full-chip or physical proof')
    (args.output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))

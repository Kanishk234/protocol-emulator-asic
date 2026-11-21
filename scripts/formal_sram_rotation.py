#!/usr/bin/env python3
"""Prove slot gating on the actual chip RTL with symbolic SRAM data."""
from pathlib import Path

from formal_channels import ROOT, run


def main():
    output = ROOT / 'build/trw-rotation'
    output.mkdir(parents=True, exist_ok=True)
    source = (ROOT / 'src/trw_chip.v').read_text()
    properties = (ROOT / 'formal/props/sram_rotation.vh').read_text()
    assert source.count('endmodule') == 1
    chip = output / 'trw_chip.v'
    chip.write_text(source.replace('endmodule', properties + 'endmodule'))
    src = ROOT / 'src'
    sources = ' '.join(str(path) for path in sorted(src.glob('*.v')) if path.name != chip.name)
    config = output / 'rotation.sby'
    config.write_text(f"""[tasks]
safety proof
reachable cover

[options]
proof: mode prove
cover: mode cover
cover: depth 8

[engines]
proof: abc pdr
cover: smtbmc z3

[script]
read_verilog -sv -nosynthesis -I{src} {sources}
read -formal -sv -I{src} {chip}
prep -top trw_chip -flatten
reachable: chformal -assert -remove
reachable: opt_clean -purge
delete t:RM_IHPSG13_1P_512x16_c2_bm_bist
techmap
opt -fast
setundef -undriven -anyseq
""")
    run(config, ROOT, 'safety', output / 'safety', 'PASS', 'abc pdr')
    run(config, ROOT, 'reachable', output / 'reachable', 'PASS', 'smtbmc z3')


if __name__ == '__main__':
    main()

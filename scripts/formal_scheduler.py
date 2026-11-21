#!/usr/bin/env python3
"""Check lane arbitration and flag interlocks under the proved fabric contract."""
from formal_channels import ROOT, run


def insert(source, anchor, properties):
    if source.count(anchor) != 1:
        raise ValueError(f'Expected one instrumentation anchor: {anchor}')
    return source.replace(anchor, properties + anchor)


def prove(top, dependency, properties, depth):
    src = ROOT / 'src'
    prop_dir = ROOT / 'formal/props'
    output = ROOT / 'build/formal_scheduler' / top
    output.mkdir(parents=True, exist_ok=True)
    source = (src / f'{top}.v').read_text()
    for anchor, path in properties:
        source = insert(source, anchor, (prop_dir / path).read_text())
    instrumented = output / f'{top}.v'
    instrumented.write_text(source)
    config = output / 'proof.sby'
    config.write_text(f"""[tasks]
safety proof
reachable cover

[options]
proof: mode prove
cover: mode cover
cover: depth {depth}

[engines]
proof: abc pdr
cover: smtbmc z3

[script]
read_verilog -formal -nosynthesis -sv -I{src} {instrumented} {src / dependency}
prep -top {top} -flatten
techmap
opt -fast
setundef -anyseq
""")
    run(config, ROOT, 'safety', output / 'safety', 'PASS', 'abc pdr')
    run(config, ROOT, 'reachable', output / 'reachable', 'PASS', 'smtbmc z3')


def main():
    prove('trw_fabric', 'trw_chan_port.v', [('endmodule', 'scheduler_fabric.vh')], 8)
    prove('trw_lane', 'trw_alu.v', [
        ('        end\n    endgenerate', 'scheduler_slot.vh'),
        ('endmodule', 'scheduler_lane.vh'),
    ], 12)


if __name__ == '__main__':
    main()

"""Generate a read-only configuration witness from CSV, not generated RTL.

This checks storage in a mapped held tile; it is not a user-circuit oracle.
"""
import argparse
import csv
import io
import json
import re
from pathlib import Path

from tools.fabric_audit.configmem import audit, indices


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mapping', type=Path)
    parser.add_argument('netlist', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    data = args.mapping.read_text()
    audit(data, frame_width=32, frames=20, expected_bits=616)
    mapping = {}
    for row in csv.DictReader(io.StringIO(data)):
        mask = row['used_bits_mask'].replace('_', '').strip()
        positions = [31-i for i, bit in enumerate(mask) if bit == '1']
        mapping[int(row['frame_index'])] = list(zip(positions, indices(row['ConfigBits_ranges'])))
    operations = [(frame, 0) for frame in range(20)]
    for background in (0, 0xffffffff):
        operations += [(frame, background) for frame in range(20)]
        for frame in range(20):
            for bit in range(32):
                operations += [(frame, background ^ (1 << bit)), (frame, background)]
    expected = 0
    vectors = []
    for frame, word in operations:
        for source, dest in mapping[frame]:
            expected = (expected & ~(1 << dest)) | (((word >> source) & 1) << dest)
        vectors.append((frame, word, expected))
    args.output.mkdir(parents=True, exist_ok=True)
    for name, width, column in [('frames', 2, 0), ('words', 8, 1), ('expected', 154, 2)]:
        (args.output/f'{name}.hex').write_text(''.join(f'{v[column]:0{width}x}\n' for v in vectors))
    module = json.loads(args.netlist.read_text())['modules']['LUT4AB']
    declarations, connections = [], []
    for name, port in module['ports'].items():
        assert re.fullmatch(r'\w+', name), name
        width = len(port['bits'])
        if port['direction'] == 'input':
            declarations.append(f'reg [{width-1}:0] {name} = {1 if name == "ReloadHold" else 0};')
        else:
            declarations.append(f'wire [{width-1}:0] {name};')
        connections.append(f'.{name}({name})')
    count = len(vectors)
    tb = '''`timescale 1ns/1ps
module tile_storage_tb;
DECLARATIONS
LUT4AB dut (CONNECTIONS);
reg [7:0] frames [0:LAST];
reg [31:0] words [0:LAST];
reg [615:0] expected [0:LAST];
reg [615:0] want;
integer i, checks=0;
initial begin
  $readmemh("frames.hex", frames);
  $readmemh("words.hex", words);
  $readmemh("expected.hex", expected);
  #5;
  for (i=0; i<COUNT; i=i+1) begin
    FrameData=~words[i]; FrameStrobe=20'b1 << frames[i]; #2;
    // Change data while the gate is open: a flip-flop substitution must fail.
    FrameData=words[i]; #2;
    want=expected[i];
    if ($test$plusargs("wrong_expected")) want=want ^ 616'b1;
    if (i>=19) begin
      if (dut.ConfigBits !== want) $fatal(1,"FAIL: tile configuration transparent capture at vector %0d",i);
      checks=checks+1;
    end
    FrameStrobe=0; #2; FrameData=~words[i]; #2;
    if (i>=19) begin
      if (dut.ConfigBits !== want) $fatal(1,"FAIL: tile configuration closed-gate retention at vector %0d",i);
      checks=checks+1;
    end
  end
  $display("PASS: mapped held-tile configuration: %0d vectors, %0d full-bank checks",COUNT,checks);
  $finish;
end
endmodule
'''
    for old, new in [('DECLARATIONS', '\n'.join(declarations)), ('CONNECTIONS', ', '.join(connections)), ('LAST', str(count-1)), ('COUNT', str(count))]:
        tb = tb.replace(old, new)
    (args.output/'tile_storage_tb.v').write_text(tb)
    (args.output/'vectors.json').write_text(json.dumps({'vectors': count, 'mapped_bits':616, 'frames':20, 'padding_bits':24, 'scope':'internal read-only configuration witness; held tile, no user behavior or timing claim'}, indent=2)+'\n')


if __name__ == '__main__':
    main()

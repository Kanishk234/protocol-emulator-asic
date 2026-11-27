#!/usr/bin/env python3
"""Prove host slot write decoding for arbitrary decoded SPI commands."""
import re
import subprocess

from formal_channels import ROOT


def main():
    source = (ROOT / 'src/trw_host.v').read_text()
    # Replace only the transport with unconstrained decoded writes.
    source, count = re.subn(
        r'(?ms)^    trw_spi u_spi \(.*?^    \);$',
        '''    (* anyseq *) reg decoded_wr;
    (* anyseq *) reg [15:0] decoded_addr, decoded_data;
    assign wr = decoded_wr;
    assign wa = decoded_addr;
    assign wd = decoded_data;
    assign {rd_req, rd_ack, rd_done, ra, miso} = 20'b0;''',
        source,
    )
    guard = ' && !run[g];'
    if count != 1 or source.count(guard) != 1 or source.count('endmodule') != 1:
        raise ValueError('Unexpected host transport or slot guard')
    property_source = """
    genvar lane;
    generate for (lane = 0; lane < NL; lane = lane + 1) begin : g_slot_proof
        always @* assert(slot_we[lane] ==
            (wr && (wa[15:10] == 6'd4) && (wa[9:8] == lane) &&
             (wa[3:2] == 2'b00) && !run[lane]));
    end endgenerate
"""
    source = source.replace('endmodule', property_source + 'endmodule')
    output = ROOT / 'build/formal_host_slots'
    output.mkdir(parents=True, exist_ok=True)
    for name, rtl, expected in (
        ('native', source, 'no model found: SUCCESS!'),
        ('unguarded', source.replace(guard, ';'), 'model found: FAIL!'),
    ):
        file = output / f'{name}.v'
        file.write_text(rtl)
        command = (f'read_verilog -formal -sv -I src build/formal_host_slots/{name}.v; '
                   'prep -top trw_host; chformal -lower; opt_clean -purge; '
                   'sat -seq 1 -prove-asserts')
        result = subprocess.run(['yosys', '-QT', '-p', command], cwd=ROOT,
                                check=True, capture_output=True, text=True)
        (output / f'{name}.log').write_text(result.stdout)
        if expected not in result.stdout:
            raise RuntimeError(f'Unexpected slot proof result for {name}')
        print(f'{name}: {expected}')


if __name__ == '__main__':
    main()

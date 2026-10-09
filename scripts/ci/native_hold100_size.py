"""Six measured strength changes; exact source, unchanged logical wiring."""
import argparse
import hashlib
import json
from pathlib import Path
from event_nor2_screen import logical_cells

SOURCE_SHA256 = 'c4461934d2faf14ea22593a1ff3201473cbbd064252e5252b094ea7c2305760b'
TARGETS = (
    ('place7221', 'buf_1', 'buf_4', {'A': '_19292_', 'X': 'net7221'}),
    ('_37732_', 'nand2_1', 'nand2_2', {'A': '_11905_', 'B': 'net7395', 'Y': '_11923_'}),
    ('_24896_', 'nor2_1', 'nor2_2', {'A': '_19307_', 'B': '_19312_',
                                   'Y': '\\u_chip.g_unit[0].u_unit.c_in '}),
    ('_29918_', 'nor3_1', 'nor3_2', {'A': '\\u_chip.g_unit[0].u_unit.g_bs.u_bs.smp_done ',
                                    'B': '_04771_', 'C': '_04775_', 'Y': '_04776_'}),
    ('_38013_', 'nor4_1', 'nor4_2', {'A': 'net6617', 'B': '_11697_', 'C': '_11701_',
                                   'D': '_12189_', 'Y': '_12190_'}),
    ('_30044_', 'a21oi_1', 'a21oi_2', {'A1': '_18837_', 'A2': '_04899_',
                                     'B1': '_18868_', 'Y': '_04902_'}),
)


def validate_change(before, after):
    original, changed = logical_cells(before), logical_cells(after)
    for name, old, new, pins in TARGETS:
        expected = ('sg13cmos5l_' + old, tuple(sorted(pins.items())))
        if original.get(name) != expected:
            raise ValueError('Native target identity/connectivity mismatch or repeated repair')
        original[name] = ('sg13cmos5l_' + new, expected[1])
    if original != changed:
        raise ValueError('Native sizing changed additional logic or wiring')


def target_call():
    # Verilog escaped identifiers are plain hierarchical names in OpenDB.
    def word(value):
        value = value.strip().removeprefix('\\')
        if any(c in value for c in '{}\n\r'):
            raise ValueError('Unsafe Tcl target')
        return '{' + value + '}'
    rows = []
    for name, old, new, pins in TARGETS:
        nets = ' '.join(word(pin) + ' ' + word(net) for pin, net in pins.items())
        rows.append('{' + ' '.join([word(name), word('sg13cmos5l_' + old),
                    word('sg13cmos5l_' + new), '{' + nets + '}']) + '}')
    return 'tripwire_size_native_hold100 {\n' + '\n'.join(rows) + '\n}\n'


def prepare(source, output):
    if hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError('Unreviewed extracted hold100 source')
    cells = logical_cells(source.read_text())
    for name, old, _, pins in TARGETS:
        if cells.get(name) != ('sg13cmos5l_' + old, tuple(sorted(pins.items()))):
            raise ValueError('Native source target mismatch')
    output.write_text(target_call())
    return {'source_run': 37870374707, 'source_sha256': SOURCE_SHA256,
            'changes': len(TARGETS), 'physical_qualification_required': True,
            'official_signoff': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.output), indent=2))

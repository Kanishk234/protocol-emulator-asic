"""Twelve measured clock8 strength changes; exact source, unchanged logical wiring."""
import argparse
import hashlib
import json
from pathlib import Path
from event_nor2_screen import logical_cells

SOURCE_SHA256 = 'f4098dfd7ac36eb044867ab6d8728c98a58f0ce1754b60d7ba0d0e47b9f0a43e'
DRT_SHA256 = '15eba6e2995b1235d8372e81c9063e95ce9de3558cf283f320b879549767c019'
TARGETS = (('_24812_', 'inv_1', 'inv_4', {'A': '_19231_', 'Y': '\\u_chip.g_unit[2].u_unit.b_in '}),
 ('_24876_', 'inv_1', 'inv_4', {'A': '_19293_', 'Y': '\\u_chip.g_unit[0].u_unit.a_in '}),
 ('_24896_',
  'nor2_1',
  'nor2_2',
  {'A': '_19307_', 'B': '_19312_', 'Y': '\\u_chip.g_unit[0].u_unit.c_in '}),
 ('_29918_',
  'nor3_1',
  'nor3_2',
  {'A': '\\u_chip.g_unit[0].u_unit.g_bs.u_bs.smp_done ',
   'B': '_04771_',
   'C': '_04775_',
   'Y': '_04776_'}),
 ('_30044_',
  'a21oi_1',
  'a21oi_2',
  {'A1': '_18837_', 'A2': '_04899_', 'B1': '_18868_', 'Y': '_04902_'}),
 ('_37732_', 'nand2_1', 'nand2_2', {'A': '_11905_', 'B': 'net7395', 'Y': '_11923_'}),
 ('_38013_',
  'nor4_1',
  'nor4_2',
  {'A': 'net6617', 'B': '_11697_', 'C': '_11701_', 'D': '_12189_', 'Y': '_12190_'}),
 ('place6636', 'buf_1', 'buf_4', {'A': 'net6637', 'X': 'net6636'}),
 ('place6637', 'buf_1', 'buf_4', {'A': '_11668_', 'X': 'net6637'}),
 ('place7221', 'buf_1', 'buf_4', {'A': '_19292_', 'X': 'net7221'}),
 ('place7311', 'buf_1', 'buf_4', {'A': 'net7312', 'X': 'net7311'}),
 ('place8245', 'buf_1', 'buf_4', {'A': 'net12432', 'X': 'net8245'}))


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
    # Escaping follows the previously exercised hold100 physical binding.
    # Clock8 ODB application still requires an independently qualified screen.
    def word(value):
        value = value.strip().removeprefix('\\')
        value = value.replace('[', '\\[').replace(']', '\\]')
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
    if output.exists() or output.resolve() == source.resolve():
        raise ValueError("Refusing to replace existing source or targets")
    if hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError('Unreviewed extracted clock8 source')
    cells = logical_cells(source.read_text())
    for name, old, _, pins in TARGETS:
        if cells.get(name) != ('sg13cmos5l_' + old, tuple(sorted(pins.items()))):
            raise ValueError('Native source target mismatch')
    output.write_text(target_call())
    return {'source_run': 37998284236, 'source_sha256': SOURCE_SHA256,
            'changes': len(TARGETS), 'physical_qualification_required': True,
            'official_signoff': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.output), indent=2))

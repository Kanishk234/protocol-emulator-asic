import json
import re

import pytest

from guarded_word_probe import PROTECTION_RX, connectivity, logged_objects, main


def netlist():
    cells = []
    for group, count in [(0, 6), (1, 1)]:
        base = f'u.g_pair[0].g_group[{group}]'
        for side in [0, 1]:
            node = f'{base}.trw_guard_mask{side}_node'
            prefix = base + ('.g_second' if side else '')
            cells.append(f'sg13cmos5l_buf_2 \\{prefix}.mask{side}_driver (.A(src{side}), .X(\\{node} ));')
            cells.append(f'sg13cmos5l_antennanp \\{prefix}.trw_guard_mask{side}_diode (.A(\\{node} ));')
        for bit in range(count):
            cells.append(f'sg13cmos5l_a22oi_1 \\{base}.g_bit[{bit}].g_used.trw_guard_sink '
                         f'(.A1(\\{base}.trw_guard_mask0_node ), .A2(data0), '
                         f'.B1(\\{base}.trw_guard_mask1_node ), .B2(data1), .Y(y{group}_{bit}));')
    return '\n'.join(cells)


def test_intact():
    result = connectivity(netlist())
    assert result['connectivity_preserved']
    assert result['guarded_gate_count'] == 7
    assert len(result['protected_objects']) == 8


@pytest.mark.parametrize('mutation', ['diode', 'sink', 'function', 'driver', 'missing'])
def test_broken_protection(mutation):
    text = netlist()
    if mutation == 'diode':
        text = re.sub(r'(trw_guard_mask0_diode \(\.A\()[^)]*', r'\1wrong', text, count=1)
    elif mutation == 'sink':
        text = text.replace('.A1(\\u.g_pair[0].g_group[0].trw_guard_mask0_node )', '.A1(split_net)', 1)
    elif mutation == 'function':
        text = text.replace('sg13cmos5l_a22oi_1', 'sg13cmos5l_a21oi_1', 1)
    elif mutation == 'driver':
        text = text.replace('sg13cmos5l_buf_2', 'sg13cmos5l_inv_2', 1)
    else:
        text = text.replace('trw_guard_sink', 'missing', 1)
    assert not connectivity(text)['connectivity_preserved']


def test_data_paths_remain_repairable():
    for name in ['u.mask0_driver', 'u.mask1_driver', 'u.trw_guard_sink', 'u.data_driver']:
        assert not re.search(PROTECTION_RX, name)
    assert re.search(PROTECTION_RX, 'u.trw_guard_mask0_node')


@pytest.mark.parametrize('missing_object', [False, True])
@pytest.mark.parametrize('escaped', [False, True])
def test_every_protected_object_must_be_logged(tmp_path, monkeypatch, missing_object, escaped):
    p = tmp_path / '4-openroad-resizertimingpostgrt'
    p.mkdir()
    text = netlist()
    (p / 'probe.nl.v').write_text(text)
    objects = connectivity(text)['protected_objects']
    for i, stage in enumerate(['repairdesignpostgpl', 'resizertimingpostcts',
                               'repairdesignpostgrt', 'resizertimingpostgrt']):
        path = tmp_path / f'{i}-openroad-{stage}'
        path.mkdir(exist_ok=True)
        names = objects[:-1] if missing_object and i == 0 else objects
        messages = []
        for name in names:
            kind = 'Net' if name.endswith('_node') else 'Instance'
            printed = name.replace('[', r'\[').replace(']', r'\]') if escaped else name
            messages.append(f"[INFO] {kind} '{printed}' matched don't touch regular expression, "
                            "setting as don't touch…")
        (path / f'openroad-{stage}.log').write_text('\n'.join(messages))
    (tmp_path / 'resolved.json').write_text(json.dumps({'RSZ_DONT_TOUCH_RX': PROTECTION_RX}))
    p = tmp_path / '5-openroad-stamidpnr-3'
    p.mkdir()
    (p / 'or_metrics_out.json').write_text(json.dumps({'timing__setup__ws__corner:typ': 1}))
    monkeypatch.setattr('sys.argv', ['probe', str(tmp_path), '--protected', 'true'])
    if missing_object:
        with pytest.raises(ValueError, match='Missing complete native protection log evidence'):
            main()
    else:
        main()


def test_note_is_not_native_protection_evidence():
    assert not logged_objects("Note 'u.trw_guard_mask0_node' matched don't touch regular expression")


def test_object_kind_is_preserved():
    text = "[INFO] Instance 'u.trw_guard_mask0_node' matched don't touch regular expression, setting as don't touch…"
    assert ('Net', 'u.trw_guard_mask0_node') not in logged_objects(text)

import pytest
from native_hold100_size import TARGETS, validate_change, prepare


def netlist(changed=False):
    rows = []
    for name, old, new, pins in TARGETS:
        ports = ', '.join('.' + pin + '(' + net + ')' for pin, net in pins.items())
        rows.append('sg13cmos5l_' + (new if changed else old) + ' ' + name + ' (' + ports + ');')
    return '\n'.join(rows)


def test_exact_six_changes():
    validate_change(netlist(), netlist(True))


@pytest.mark.parametrize('mutation', ['wire', 'extra', 'missing', 'repeat'])
def test_no_unreviewed_logic_or_repeat(mutation):
    before, after = netlist(), netlist(True)
    if mutation == 'wire': after = after.replace('net7221', 'other')
    if mutation == 'extra': after += '\nsg13cmos5l_buf_1 extra(.A(a), .X(b));'
    if mutation == 'missing': after = after.replace('sg13cmos5l_buf_4', 'sg13cmos5l_buf_1')
    if mutation == 'repeat': before = netlist(True)
    with pytest.raises(ValueError):
        validate_change(before, after)


def test_source_hash_required_before_writing(tmp_path):
    source, output = tmp_path / 'source.v', tmp_path / 'targets.tcl'
    source.write_text(netlist())
    with pytest.raises(ValueError, match='Unreviewed extracted'):
        prepare(source, output)
    assert not output.exists()


def test_multiline_sram_bus_rewire_is_rejected():
    macro = '\nRM_IHPSG13_1P_512x16_c2_bm_bist s (.A_ADDR({a,\nb}), .A_DOUT({c,\nd}));'
    before = netlist() + macro
    validate_change(before, netlist(True) + macro)
    with pytest.raises(ValueError, match='additional logic or wiring'):
        validate_change(before, netlist(True) + macro.replace('b}', 'other}'))

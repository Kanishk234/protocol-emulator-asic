import pytest
from native_clock8_size import TARGETS, validate_change, prepare, target_call


def netlist(changed=False):
    rows = []
    for name, old, new, pins in TARGETS:
        ports = ', '.join('.' + pin + '(' + net + ')' for pin, net in pins.items())
        rows.append('sg13cmos5l_' + (new if changed else old) + ' ' + name + ' (' + ports + ');')
    return '\n'.join(rows)


def test_exact_twelve_changes():
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


def test_generated_names_match_observed_odb_bracket_escaping():
    call = target_call()
    assert '{u_chip.g_unit\\[0\\].u_unit.c_in}' in call
    assert '{u_chip.g_unit\\[0\\].u_unit.g_bs.u_bs.smp_done}' in call
    assert '{u_chip.g_unit[0].u_unit.c_in}' not in call


def test_distinct_exported_and_drt_hashes():
    from native_clock8_size import SOURCE_SHA256, DRT_SHA256
    assert SOURCE_SHA256 == 'f4098dfd7ac36eb044867ab6d8728c98a58f0ce1754b60d7ba0d0e47b9f0a43e'
    assert DRT_SHA256 == '15eba6e2995b1235d8372e81c9063e95ce9de3558cf283f320b879549767c019'
    assert SOURCE_SHA256 != DRT_SHA256

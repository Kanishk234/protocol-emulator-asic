import pytest
from actual_endpoint_diodes import TARGETS, verify_edit, violating_sinks


def design(insert=False):
    names = [t.split('/')[0] for t in TARGETS]
    cells = '\n'.join(f'- {n} sg13cmos5l_buf_2 + PLACED ( 1000 2000 ) N ;' for n in names)
    if insert:
        cells += '\n' + '\n'.join(f'- eco_diode_{i} sg13cmos5l_antennanp + PLACED ( 1200 2000 ) N ;' for i in range(4))
    nets = '\n'.join(f'- {net} ( {t.split("/")[0]} A )'
                     + (f' ( eco_diode_{i} A )' if insert else '') + ' ;'
                     for i, (t, net) in enumerate(TARGETS.items()))
    return f'\nCOMPONENTS {4 + 4 * insert} ;\n{cells}\nEND COMPONENTS\nNETS 4 ;\n{nets}\nEND NETS\n'


def test_four_diodes_and_empty_control():
    assert verify_edit(design(), design(True), True) == 4
    assert verify_edit(design(), design(), False) == 0


def test_violations_are_per_pin_and_deduplicated():
    report = 'Net: a\n  Pin: x/A (buf)\n(VIOLATED)\n(VIOLATED)\n  Pin: y/A (buf)\nclean\nNet: b\n  Pin: z/B (nor)\n(VIOLATED)\n'
    assert violating_sinks(report) == {'x/A', 'z/B'}


def test_clean_report_has_no_violations():
    assert violating_sinks('') == set()


@pytest.mark.parametrize('mutation', ['position', 'master', 'diode_net', 'sink_net'])
def test_wrong_edit_rejected(mutation):
    after = design(True)
    if mutation == 'position': after = after.replace('1000 2000', '2000 2000', 1)
    if mutation == 'master': after = after.replace('sg13cmos5l_buf_2', 'sg13cmos5l_buf_4', 1)
    if mutation == 'diode_net': after = after.replace('( eco_diode_0 A )', '( eco_diode_0 B )')
    if mutation == 'sink_net': after = after.replace('( hold7969 A )', '( hold7969 B )')
    with pytest.raises(ValueError):
        verify_edit(design(), after, True)

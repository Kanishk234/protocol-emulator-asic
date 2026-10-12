import pytest
from extracted_hold_targets import endpoints,plan


def report(endpoint='_46591_',slack='.000022',kind='rising edge-triggered flip-flop'):
    return f'nom_fast_1p32V_m40C\nStartpoint: latch\nEndpoint: {endpoint} ({kind} clocked by clk)\n {slack} slack (MET)\n'


def test_selects_only_sub_gate_endpoints_and_deduplicates_worst():
    text=report()+report(slack='.02')+report('_other_', '.06')
    assert endpoints(text)=={'_46591_':.000022}


@pytest.mark.parametrize('bad',[report(kind='positive level-sensitive latch'),report().replace('nom_fast_1p32V_m40C','nom_slow_1p08V_125C'),report(slack='.06'),report().replace(' .000022 slack (MET)',''),report()+' .01 slack (MET)\n'])
def test_wrong_corner_missing_paths_or_unreviewed_endpoints_fail(bad):
    with pytest.raises(ValueError):endpoints(bad)


def test_exact_source_binding_rejects_unreviewed_inputs(tmp_path):
    with pytest.raises(ValueError,match='Wrong extracted hold source'):plan('wrong','wrong',report(),tmp_path/'std.lef')

"""Native fixture evidence classification, without running any EDA locally."""
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'test_internal'))
import cloud_router_regression as regression


def route(name='n1', x=10):
    return f'{name}\n(\n0 0 metal1 {x} 0 metal1\n{x} 0 metal1 {x} 0 metal2\n)\n'


TABLE = 'Final congestion report:\nmetal1 100 10 10.00% 0 / 0 / 0\nTotal 100 10 10.00% 0 / 0 / 0\n'


@pytest.fixture
def evidence(tmp_path):
    stock, custom = tmp_path/'stock', tmp_path/'custom'
    stock.mkdir(); custom.mkdir()
    segments = route('n1')+route('n2')+route('unselected')
    census = 'INST\tu\tmaster\t0 0\tR0\tPLACED\n'
    for name in ('n1', 'n2', 'unselected'):
        census += f'PORT\t{name}a\tINPUT\tSIGNAL\t{name}\nPORT\t{name}b\tOUTPUT\tSIGNAL\t{name}\n'
    guides = ''.join(f'NET\t{name}\t2\t3\t0\n' for name in ('n1', 'n2', 'unselected'))
    for directory in (stock, custom):
        for kind, text in [('segments.txt', segments), ('census.tsv', census), ('guides.tsv', guides)]:
            (directory/f'before-{kind}').write_text(text)
    for case in ('duplicate', 'null', 'clock', 'after'):
        for kind in ('segments.txt', 'census.tsv', 'guides.tsv'):
            (custom/f'{case}-{kind}').write_bytes((custom/f'before-{kind}').read_bytes())
    (custom/'selected.tsv').write_text('SELECTED\tn1\nSELECTED\tn2\n')
    (custom/'invalid-cases.tsv').write_text('INVALID\tduplicate\tREJECTED\nINVALID\tnull\tREJECTED\nINVALID\tclock\tREJECTED\n')
    (stock/'native.log').write_text(TABLE)
    (custom/'native.log').write_text(TABLE+regression.MARKER+'\n[INFO GRT-0009] rerouting 2 nets.\n'+TABLE+'WARP_REGRESSION_FORCE_COMPLETE\n')
    return stock, custom


def test_complete_native_evidence_passes_with_explicit_scope(evidence):
    result = regression.validate(*evidence)
    assert result['passed'] and not result['physical_acceptance']
    assert result['actual_case_counts'] == {'default_tools': 2, 'invalid_rejections': 3, 'forced_pair': 1}
    assert result['complete_native_route_count'] == 3
    assert result['selected_routes_changed'] == []  # Re-execution is witnessed by native logger.


def test_unselected_route_change_rejects(evidence):
    stock, custom = evidence
    (custom/'after-segments.txt').write_text(route('n1')+route('n2')+route('unselected', 20))
    with pytest.raises(ValueError, match='Unselected'):
        regression.validate(stock, custom)


def test_selected_change_allowed_after_actual_reroute(evidence):
    stock, custom = evidence
    (custom/'after-segments.txt').write_text(route('n1', 20)+route('n2')+route('unselected'))
    assert regression.validate(stock, custom)['selected_routes_changed'] == ['n1']


def test_default_mapping_hash_mismatch_rejects(evidence):
    stock, custom = evidence
    (stock/'before-segments.txt').write_text(route('n1', 20)+route('n2')+route('unselected'))
    with pytest.raises(ValueError, match='default native segments differ'):
        regression.validate(stock, custom)


@pytest.mark.parametrize('case', ['duplicate', 'null', 'clock'])
def test_invalid_call_state_mutation_rejects(evidence, case):
    stock, custom = evidence
    (custom/f'{case}-census.tsv').write_text('changed')
    with pytest.raises(ValueError, match='Invalid call mutated'):
        regression.validate(stock, custom)


@pytest.mark.parametrize('replacement', ['1', '0', '3'])
def test_noop_or_wrong_reroute_census_rejects(evidence, replacement):
    stock, custom = evidence
    path = custom/'native.log'
    path.write_text(path.read_text().replace('rerouting 2', 'rerouting '+replacement))
    with pytest.raises(ValueError, match='two-net reroute witness'):
        regression.validate(stock, custom)


def test_final_native_table_missing_rejects(evidence):
    stock, custom = evidence
    (custom/'native.log').write_text(TABLE+regression.MARKER+'\n[INFO GRT-0009] rerouting 2 nets.\nWARP_REGRESSION_FORCE_COMPLETE\n')
    with pytest.raises(ValueError, match='Missing native final'):
        regression.validate(stock, custom)


def test_physical_change_rejects(evidence):
    stock, custom = evidence
    (custom/'after-census.tsv').write_text('changed')
    with pytest.raises(ValueError, match='Physical instance'):
        regression.validate(stock, custom)


def test_incomplete_actual_invalid_cases_rejects(evidence):
    stock, custom = evidence
    (custom/'invalid-cases.tsv').write_text('INVALID\tduplicate\tREJECTED\n')
    with pytest.raises(ValueError, match='invalid-case census'):
        regression.validate(stock, custom)


def test_missing_final_guides_rejects(evidence):
    stock, custom = evidence
    path = custom/'after-guides.tsv'
    path.write_text(path.read_text().replace('NET\tn1\t2\t3', 'NET\tn1\t2\t0'))
    with pytest.raises(ValueError, match='guides incomplete'):
        regression.validate(stock, custom)


@pytest.mark.parametrize('text', ['', route()+route(), 'n\n(\n0 0 metal1 10 10 metal1\n)\n', 'n\n(\n0 0 metal1 10 0 metal2\n)\n', 'n\n(\n0 0 invalid 10 0 invalid\n)\n'])
def test_bad_native_segments_rejected(text):
    with pytest.raises(ValueError):
        regression.segments(text)


def test_reversed_segment_orientation_preserves_mapping():
    original = route()
    changed = original.replace('0 0 metal1 10 0 metal1', '10 0 metal1 0 0 metal1')
    assert regression.segments(original) == regression.segments(changed)


def test_tcl_keeps_clock_restore_actual_cases_and_native_force_order():
    text = (regression.ROOT/'tools/router_build/regression.tcl').read_text()
    assert '[$net getGuides]] > 2' in text
    assert '$warp_first setSigType $warp_signal_type' in text
    assert text.index('$warp_first setSigType $warp_signal_type') < text.index('puts "WARP_REGRESSION_FORCE_BEGIN"')
    for case in ('duplicate', 'null', 'clock'):
        assert f'warp_rejected {case} ' in text
    assert 'global_route -verbose' in text
    assert '-allow_congestion' not in text

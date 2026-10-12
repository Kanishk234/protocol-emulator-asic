import pytest
from route_segment_audit import parse,compare

A='net\n(\n0 0 Metal2 10 0 Metal2\n10 0 Metal2 10 0 Metal3\n)\n'


def test_roundtrip_allows_direction_and_order_only():
    b='net\n(\n10 0 Metal3 10 0 Metal2\n10 0 Metal2 0 0 Metal2\n)\n'
    x=compare(A,b)
    assert x['exact_roundtrip'] and x['unchanged_routes_preserved']
    assert not x['physical_timing_measured'] and not x['official_signoff']


def test_new_route_or_geometry_must_be_explicitly_allowed():
    b=A.replace('10 0','20 0')
    assert not compare(A,b)['unchanged_routes_preserved']
    assert compare(A,b,['net'])['unchanged_routes_preserved']
    assert not compare(A,A+A.replace('net','new'))['unchanged_routes_preserved']


def test_duplicate_segment_multiplicity_preserved():
    b=A.replace(')\n','0 0 Metal2 10 0 Metal2\n)\n')
    assert not compare(A,b)['exact_roundtrip']


@pytest.mark.parametrize('text',['',A[:-2],A+A,A.replace('10 0 Metal2','10 5 Metal2'),A.replace('0 0 Metal2 10','wrong 0 Metal2 10')])
def test_incomplete_or_invalid_exports_refused(text):
    with pytest.raises(ValueError):parse(text)

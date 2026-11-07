import pytest

from host_align_congestion_readback import parse_guides, match_guides, source_manifest


def test_only_reviewed_source_manifests(monkeypatch):
    monkeypatch.delenv('SOURCE_MANIFEST', raising=False)
    assert source_manifest().name == 'host_align_congestion_source.json'
    monkeypatch.setenv('SOURCE_MANIFEST','spikes/phase2_stock_flow/host_idle_congestion_source.json')
    assert source_manifest().name == 'host_idle_congestion_source.json'
    monkeypatch.setenv('SOURCE_MANIFEST','/tmp/unreviewed.json')
    with pytest.raises(ValueError,match='Unreviewed'):
        source_manifest()


def test_guides_match_only_same_layer_and_whole_edge():
    guides = parse_guides('data\n(\n0 0 14400 7200 Metal3\n)\nother\n(\n0 0 14400 7200 Metal2\n)\n')
    edge = dict(layer='Metal3', start_dbu=[3600,3600], end_dbu=[10800,3600])
    assert match_guides(guides,[edge])[0]['guide_overlap_candidates'] == ['data']
    edge['end_dbu'] = [18000,3600]
    with pytest.raises(ValueError,match='no guide'):
        match_guides(guides,[edge])


@pytest.mark.parametrize('text', ['a\n(\n)', 'a\n(\n0 0 0 1 Metal3\n)', 'a\n(\n0 0 1 1 Metal3', 'a\n(\n0 0 1 1 Metal3\n)\na'])
def test_bad_or_duplicate_guides_reject(text):
    with pytest.raises(ValueError):
        parse_guides(text)

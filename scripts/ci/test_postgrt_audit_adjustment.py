from pathlib import Path

import pytest

from postgrt_timing import audit_grt_adjustment


def test_legacy_callers_keep_original_value():
    assert audit_grt_adjustment(Path('before'), None, None) == 0.16
    assert audit_grt_adjustment(Path('before'), Path('after'), None) == 0.16


def test_read_only_audit_keeps_actual_source_value():
    assert audit_grt_adjustment(Path('source'), Path('./source'), 0.15) == 0.15


@pytest.mark.parametrize('after', [None, Path('other')])
def test_override_cannot_enable_a_physical_repair(after):
    with pytest.raises(ValueError, match='same read-only checkpoint'):
        audit_grt_adjustment(Path('source'), after, 0.15)


@pytest.mark.parametrize('value', [-0.01, 1, float('nan'), float('inf'), '0.15', False])
def test_invalid_audit_values(value):
    with pytest.raises(ValueError, match='Invalid read-only'):
        audit_grt_adjustment(Path('source'), Path('source'), value)

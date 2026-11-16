from pathlib import Path

import pytest

from selector_integration_bundle import ROOT, bind_regression, build


def test_existing_review_payload_is_preserved(tmp_path):
    output = tmp_path / 'existing'
    output.mkdir()
    (output / 'user-file').write_text('preserve')
    with pytest.raises(ValueError, match='Preserve existing'):
        build(tmp_path, tmp_path / 'absent.zip', output)
    assert (output / 'user-file').read_text() == 'preserve'


def test_review_cannot_target_the_source_checkout(tmp_path):
    with pytest.raises(ValueError, match='outside'):
        build(tmp_path, tmp_path / 'absent.zip', ROOT / 'build/integration')


def test_unbound_archive_is_rejected_before_reading_candidate(tmp_path):
    archive = tmp_path / 'wrong.zip'
    archive.write_bytes(b'untrusted')
    with pytest.raises(ValueError, match='Wrong complete'):
        bind_regression(archive, tmp_path / 'missing-candidate')

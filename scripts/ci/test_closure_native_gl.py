import json
from pathlib import Path

import pytest

from closure_native_gl import validate, ARTIFACT_ID, ARCHIVE_SHA
from test_closure_route import context


@pytest.mark.parametrize('mutation', ['run', 'artifact', 'digest'])
def test_foreign_native_inputs_stop_before_reading_archive(tmp_path, mutation):
    run, artifact = context()
    artifact.update(id=ARTIFACT_ID, digest=ARCHIVE_SHA)
    if mutation == 'run': run['id'] = 1
    if mutation == 'artifact': artifact['id'] = 1
    if mutation == 'digest': artifact['digest'] = 'sha256:' + '0' * 64
    output = tmp_path / 'netlist.v'
    with pytest.raises(ValueError): validate(run, artifact, tmp_path / 'absent.zip', tmp_path, output)
    assert not output.exists()


def test_changed_archive_is_rejected(tmp_path):
    run, artifact = context(); artifact.update(id=ARTIFACT_ID, digest=ARCHIVE_SHA)
    archive = tmp_path / 'wrong.zip'; archive.write_bytes(b'foreign bytes')
    with pytest.raises(ValueError, match='archive bytes'):
        validate(run, artifact, archive, tmp_path, tmp_path / 'netlist.v')


def test_bound_netlist_matches_committed_authenticated_receipt():
    from closure_native_gl import NETLIST, NETLIST_SHA
    root = Path(__file__).resolve().parents[2]
    receipt = json.loads((root / 'docs/reports/closure_screen_42681697462.json').read_text())
    assert receipt['archive_sha256'] == ARCHIVE_SHA and receipt['artifact_id'] == ARTIFACT_ID
    assert receipt['frozen_views'][NETLIST] == NETLIST_SHA

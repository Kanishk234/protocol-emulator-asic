"""Identity checks for independent verification sources and retained license files."""
import hashlib
import json

import pytest
from repo_audit import verify_vendor_sources


@pytest.fixture
def package(tmp_path):
    folder = tmp_path / 'test_internal/vendor/example'
    folder.mkdir(parents=True)
    files = {'peer.v': b'module peer; endmodule\n', 'COPYING': b'License notice\n'}
    for name, data in files.items(): (folder / name).write_bytes(data)
    row = {'revision': 'a'*40, 'license_file': 'COPYING',
           'files': {n: {'sha256': hashlib.sha256(data).hexdigest()} for n, data in files.items()}}
    (folder / 'PROVENANCE.json').write_text(json.dumps(row))
    return tmp_path, folder


def test_pinned_files_and_license_match(package):
    assert verify_vendor_sources(package[0]) == 1


@pytest.mark.parametrize('change', ['source', 'license', 'revision'])
def test_changed_dependency_rejected(package, change):
    root, folder = package
    if change == 'source': (folder / 'peer.v').write_text('module other; endmodule\n')
    elif change == 'license': (folder / 'COPYING').unlink()
    else:
        path = folder / 'PROVENANCE.json'
        row = json.loads(path.read_text()); row['revision'] = 'master'
        path.write_text(json.dumps(row))
    with pytest.raises(ValueError): verify_vendor_sources(root)

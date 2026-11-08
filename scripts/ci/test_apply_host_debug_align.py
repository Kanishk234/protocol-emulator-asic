import difflib
import hashlib
import json
from pathlib import Path

import pytest

from apply_host_debug_align import apply


def fixture(tmp_path):
    root=tmp_path/'project';(root/'src').mkdir(parents=True)
    before='module cfg; endmodule\n';after='module cfg; wire q; endmodule\n'
    (root/'src/trw_host.v').write_text(before)
    (root/'src/unrelated.v').write_text('module untouched; endmodule\n')
    evidence=tmp_path/'evidence';evidence.mkdir()
    patch=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),
        fromfile='a/src/trw_host.v',tofile='b/src/trw_host.v'))
    (evidence/'host_debug_align.patch').write_text(patch)
    sha=lambda s:hashlib.sha256(s.encode()).hexdigest()
    (evidence/'evidence.json').write_text(json.dumps(dict(reference_sha256=sha(before),
        candidate_sha256=sha(after),patch_sha256=sha(patch))))
    return root,evidence


def test_only_bound_target_changes_and_reapplication_refused(tmp_path):
    root,evidence=fixture(tmp_path)
    receipt=apply(root,evidence)
    assert receipt['changed_files']==['src/trw_host.v']
    assert receipt['before']['src/unrelated.v']==receipt['after']['src/unrelated.v']
    with pytest.raises(ValueError,match='reference source'):apply(root,evidence)


@pytest.mark.parametrize('fault',['source','patch'])
def test_wrong_inputs_fail_before_mutation(tmp_path,fault):
    root,evidence=fixture(tmp_path)
    path=root/'src/trw_host.v' if fault=='source' else evidence/'host_debug_align.patch'
    path.write_text(path.read_text()+'// changed\n')
    before=(root/'src/trw_host.v').read_bytes()
    with pytest.raises(ValueError):apply(root,evidence)
    assert (root/'src/trw_host.v').read_bytes()==before


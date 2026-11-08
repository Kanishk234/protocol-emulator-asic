import difflib,hashlib,json
from pathlib import Path
import pytest
from apply_slot_enable_drive import apply


def fixture(tmp_path):
    root=tmp_path/'project';folder=tmp_path/'evidence';(root/'src').mkdir(parents=True);folder.mkdir()
    before='module slots; endmodule\n';after='module slots; wire dec; endmodule\n'
    (root/'src/trw_slots.v').write_text(before);(root/'src/other.v').write_text('module other; endmodule\n')
    patch=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/src/trw_slots.v',tofile='b/src/trw_slots.v'))
    sha=lambda t:hashlib.sha256(t.encode()).hexdigest()
    (folder/'constants.patch').write_text(patch)
    (folder/'evidence.json').write_text(json.dumps(dict(reference_sha256=sha(before),variants={'constants':dict(patch_sha256=sha(patch),candidate_sha256=sha(after))})))
    return root,folder


def test_only_expected_file_changes_and_reapplication_rejects(tmp_path):
    root,folder=fixture(tmp_path);r=apply(root,folder,'constants')
    assert r['before']['src/other.v']==r['after']['src/other.v']
    assert r['changed_files']==['src/trw_slots.v']
    with pytest.raises(ValueError,match='reference'):apply(root,folder,'constants')


@pytest.mark.parametrize('fault',['source','patch','variant'])
def test_wrong_inputs_refuse_before_source_mutation(tmp_path,fault):
    root,folder=fixture(tmp_path)
    if fault=='source':(root/'src/trw_slots.v').write_text('wrong source')
    if fault=='patch':(folder/'constants.patch').write_text('wrong patch')
    before=(root/'src/trw_slots.v').read_bytes()
    with pytest.raises(ValueError):apply(root,folder,'wrong' if fault=='variant' else 'constants')
    assert (root/'src/trw_slots.v').read_bytes()==before

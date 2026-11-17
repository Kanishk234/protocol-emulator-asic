import json
from pathlib import Path
import shutil
import pytest
from verify_integrated_candidate import verify,MANIFEST

ROOT=Path(__file__).resolve().parents[2]


def package(tmp_path):
    manifest=json.loads((ROOT/MANIFEST).read_text())
    for name in [MANIFEST,*manifest['physical_inputs'],'tools/tripwire_spec.py','.github/workflows/gds.yaml','spec/tripwire.yaml']:
        target=tmp_path/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    return tmp_path


def test_exact_integration_passes():
    result=verify(ROOT)
    assert result['physical_inputs_match'] and result['replay_encodings_match']
    assert not result['official_gds_signoff']


@pytest.mark.parametrize('name',['src/trw_pin_io.v','src/config.json','.github/workflows/gds.yaml','tools/tripwire_spec.py'])
def test_changed_qualified_input_rejected(tmp_path,name):
    root=package(tmp_path);p=root/name;p.write_bytes(p.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='Changed'):verify(root)

import json
from pathlib import Path
import shutil
import pytest
from verify_integrated_candidate import verify,MANIFEST

ROOT=Path(__file__).resolve().parents[2]


def package(tmp_path):
    manifest=json.loads((ROOT/MANIFEST).read_text())
    extra=[manifest['signoff_policy']['reference_config']] if manifest.get('signoff_policy') else []
    for name in [*extra,MANIFEST,*manifest['physical_inputs'],'tools/tripwire_spec.py','.github/workflows/gds.yaml','spec/tripwire.yaml']:
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


def test_unreviewed_physical_knob_in_policy_config_rejected(tmp_path):
    root=package(tmp_path)
    config=root/'src/config.json';value=json.loads(config.read_text());value['CLOCK_PERIOD']=25
    config.write_text(json.dumps(value))
    # Even updating the approved byte hash must not admit a physical change.
    import hashlib
    manifest=root/MANIFEST;row=json.loads(manifest.read_text())
    row['signoff_policy']['approved_config_sha256']=hashlib.sha256(config.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(row))
    with pytest.raises(ValueError,match='Physical recipe differs'):verify(root)


def test_changed_reference_config_rejected(tmp_path):
    root=package(tmp_path);row=json.loads((root/MANIFEST).read_text())
    reference=root/row['signoff_policy']['reference_config'];reference.write_bytes(reference.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='Changed qualified reference'):verify(root)

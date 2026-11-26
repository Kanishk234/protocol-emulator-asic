import hashlib
import json
from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from rtl_control_recovery import verify_model


def test_recovery_never_substitutes_changed_model_or_generated_files(tmp_path):
    source=tmp_path/'fabric.v';source.write_text('frozen model')
    data=dict(passed=True,global_tracks=4,radix='full',
              generated_sha256={'fabric.v':hashlib.sha256(source.read_bytes()).hexdigest()})
    manifest=tmp_path/'resource-control.json';manifest.write_text(json.dumps(data))
    expected=dict(tracks=4,radix='full',model_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest())
    assert verify_model(tmp_path,expected)==1
    source.write_text('changed model')
    with pytest.raises(ValueError,match='generated model file'):verify_model(tmp_path,expected)
    manifest.write_text('{}')
    with pytest.raises(ValueError,match='manifest differs'):verify_model(tmp_path,expected)

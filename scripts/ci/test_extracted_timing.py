import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from extracted_timing import route_checkpoint, preserve_signoff_constraints


def test_timeout_is_not_a_route_checkpoint(tmp_path):
    with pytest.raises(ValueError, match="completed DRT state"):
        route_checkpoint(tmp_path)


def test_route_markers_block_extraction(tmp_path):
    stage = tmp_path / "1-openroad-detailedrouting"
    stage.mkdir()
    (stage / "state_out.json").write_text(json.dumps({"metrics": {"route__drc_errors": 215}}))
    with pytest.raises(ValueError, match="zero route DRC"):
        route_checkpoint(tmp_path)


def test_completed_clean_route_files_are_required(tmp_path):
    stage = tmp_path / "1-openroad-detailedrouting"
    stage.mkdir()
    saved = tmp_path / "saved"
    saved.write_text("checkpoint")
    state = {"metrics": {"route__drc_errors": 0},
             **{key: str(saved) for key in ("odb", "def", "nl", "pnl")}}
    path = stage / "state_out.json"
    path.write_text(json.dumps(state))
    assert route_checkpoint(tmp_path) == path
    saved.unlink()
    with pytest.raises(ValueError, match="Missing final route"):
        route_checkpoint(tmp_path)


def test_effective_constraints_survive_source_removal_and_differ_from_inherited(tmp_path):
    import hashlib
    source = tmp_path / 'signoff.sdc'
    source.write_bytes(b'create_clock -period 20 [get_ports clk]\n# Live config paths timed\n')
    output = tmp_path / 'evidence'
    output.mkdir()
    inherited = output / 'inherited.sdc'
    inherited.write_text('set_false_path -setup -to [get_pins config/D]\n')
    original = source.read_bytes()
    saved = preserve_signoff_constraints(source, output)
    source.unlink()
    assert saved.read_bytes() == original
    assert saved.read_bytes() != inherited.read_bytes()
    identity = json.loads((output / 'constraint_identity.json').read_text())
    assert identity['sha256'] == hashlib.sha256(original).hexdigest()
    assert identity['sta_constraint_file'] == str(saved)
    assert identity['inherited_state_sdc_is_signoff_evidence'] is False

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from extracted_timing import route_checkpoint


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

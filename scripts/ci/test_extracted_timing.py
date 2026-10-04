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

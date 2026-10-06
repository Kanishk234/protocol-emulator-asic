import json
from pathlib import Path

import pytest

from rtl_grt_screen import checkpoint


@pytest.mark.parametrize("failure", [None, "missing_odb", "drt", "second_grt"])
def test_screen_requires_unique_complete_preroute_state(tmp_path, failure):
    source = tmp_path / "35-openroad-globalrouting/state_out.json"
    source.parent.mkdir()
    data = tmp_path / "saved"
    data.write_text("fixture")
    state = {key: str(data) for key in ("odb", "def", "nl", "pnl", "sdc")}
    if failure == "missing_odb":
        state["odb"] = str(tmp_path / "absent")
    source.write_text(json.dumps(state))
    if failure == "drt":
        (tmp_path / "44-openroad-detailedrouting").mkdir()
    if failure == "second_grt":
        other = tmp_path / "36-openroad-globalrouting/state_out.json"
        other.parent.mkdir()
        other.write_text(json.dumps(state))
    if failure:
        with pytest.raises(ValueError):
            checkpoint(tmp_path)
    else:
        assert checkpoint(tmp_path) == source

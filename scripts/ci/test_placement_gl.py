import json
from pathlib import Path
import pytest
from placement_gl import validate


@pytest.mark.parametrize("failure", [None, "gate", "drc", "state", "clock", "policy", "missing"])
def test_saved_route_identity_and_cleanliness(tmp_path, failure):
    root = tmp_path
    step = root / "runs/placement-route/drt/1-openroad-detailedrouting"
    step.mkdir(parents=True)
    (root / "src").mkdir()
    def write(path, data):
        path.write_text(json.dumps(data))
    write(root / "runs/placement-route/gates.json", {"timing_and_antenna_pass": failure != "gate"})
    write(step / "state_out.json", {"metrics": {"route__drc_errors": 1 if failure == "drc" else 0},
        "nl": "/wrong.v" if failure == "state" else "/saved/runs/placement-route/drt/1-openroad-detailedrouting/tt_um_tripwire.nl.v"})
    write(step / "config.json", {"CLOCK_PERIOD": 30 if failure == "clock" else 20,
        "GRT_ADJUSTMENT": 0.16, "PNR_SDC_FILE": "/saved/src/signoff.sdc"})
    write(root / "src/config_rx_screen.json", {"PL_TIMING_DRIVEN": failure != "policy", "PL_OPTIMIZE_MIRRORING": False})
    if failure != "missing":
        (step / "tt_um_tripwire.nl.v").write_text("module tt_um_tripwire; RM_IHPSG13_1P_512x16_c2_bm_bist ram(); endmodule")
    if failure:
        with pytest.raises((ValueError, FileNotFoundError)):
            validate(root)
    else:
        assert len(validate(root)) == 64

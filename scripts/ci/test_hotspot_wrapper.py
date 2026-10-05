import os
from pathlib import Path
import shutil
import subprocess

import pytest


@pytest.mark.parametrize("name", ["grt.tcl", "rsz_timing_postgrt.tcl", "antenna_repair.tcl", "drt.tcl", "sta.tcl"])
def test_reservation_survives_each_rerouting_entry(tmp_path, name):
    if shutil.which("tclsh") is None:
        pytest.skip("Tcl interpreter unavailable")
    bootstrap = tmp_path / "bootstrap.tcl"
    bootstrap.write_text('''
proc set_global_routing_region_adjustment {args} {puts "REGION $args"}
proc global_route {args} {puts "ROUTE $args"}
proc repair_antennas {args} {puts "ANTENNA $args"}
source [lindex $argv end]
''')
    executable = tmp_path / "openroad"
    executable.write_text('#!/usr/bin/env bash\nexec tclsh "' + str(bootstrap) + '" "$@"\n')
    executable.chmod(0o755)
    original = tmp_path / name
    original.write_text("repair_antennas diode -iterations 3\n" if name == "antenna_repair.tcl"
                        else "global_route -verbose\n")
    wrapper = Path(__file__).with_name("openroad_hotspot_wrapper.sh").resolve()
    env = dict(os.environ, PATH=str(tmp_path) + os.pathsep + os.environ["PATH"], RUNNER_TEMP=str(tmp_path))
    out = subprocess.run(["bash", str(wrapper), str(original)], env=env,
                         check=True, capture_output=True, text=True).stdout
    command = "ANTENNA" if name == "antenna_repair.tcl" else "ROUTE"
    assert ("ANTENNA diode -iterations 3" if name == "antenna_repair.tcl" else "ROUTE -verbose") in out
    if name == "sta.tcl":
        assert "REGION" not in out
    else:
        assert "REGION {500 280 700 380} -layer Metal2 -adjustment 0.30" in out
        assert out.index("REGION") < out.index(command)

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


@pytest.mark.parametrize("reads", [0, 1, 2])
def test_branch_hook_runs_after_read_and_before_routing(tmp_path, reads):
    if shutil.which("tclsh") is None:
        pytest.skip("Tcl interpreter unavailable")
    branch = tmp_path / "critical_branch.tcl"
    branch.write_text('proc tripwire_split_critical_branch {} {puts "SPLIT"}\n')
    common = tmp_path / "scripts/openroad/common"
    common.mkdir(parents=True)
    (common / "dpl.tcl").write_text('puts "LEGALIZE"\n')
    bootstrap = tmp_path / "bootstrap.tcl"
    bootstrap.write_text('''
proc set_global_routing_region_adjustment {args} {}
proc global_route {args} {puts "ROUTE"}
proc read_current_odb {} {puts "READ"}
source [lindex $argv end]
''')
    executable = tmp_path / "openroad"
    executable.write_text('#!/usr/bin/env bash\nexec tclsh "' + str(bootstrap) + '" "$@"\n')
    executable.chmod(0o755)
    original = tmp_path / "rsz_timing_postgrt.tcl"
    original.write_text("read_current_odb\n" * reads + "global_route -verbose\n")
    wrapper = tmp_path / "wrapper.sh"
    wrapper.write_text(Path(__file__).with_name("openroad_hotspot_wrapper.sh").read_text()
                       .replace("/usr/local/share/tripwire/critical_branch.tcl", str(branch)))
    # Model the minimal pinned image: awk is absent. Expose only utilities
    # already used by the wrapper plus the test's Tcl interpreter.
    for command in ("bash", "tclsh", "basename", "mktemp", "cat"):
        (tmp_path / command).symlink_to(shutil.which(command))
    env = dict(os.environ, PATH=str(tmp_path),
               RUNNER_TEMP=str(tmp_path), TRIPWIRE_BRANCH_REPAIR="1", SCRIPTS_DIR=str(tmp_path / "scripts"))
    assert shutil.which("awk", path=env["PATH"]) is None
    result = subprocess.run([shutil.which("bash"), str(wrapper), str(original)], env=env,
                            capture_output=True, text=True)
    if reads != 1:
        assert result.returncode != 0
        assert "SPLIT" not in result.stdout
    else:
        assert result.returncode == 0, result.stderr
        output = result.stdout
        assert output.index("READ") < output.index("SPLIT") < output.index("LEGALIZE") < output.index("ROUTE")
        assert output.count("SPLIT") == 1

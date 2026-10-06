"""Combinational native LUT proofs under captured configuration, on cloud only.

User state and tile inputs stay arbitrary. Sequential cells are cut to anyseq;
configuration Q values alone are constrained. This is not sequential equivalence,
four-state equivalence, timing proof, or a substitute for native simulation.
"""
import json
from pathlib import Path
import re
import subprocess


def run_proofs(root, work, library):
    out = root / "build/cloud_setup/local_lut_formal"
    out.mkdir(parents=True, exist_ok=True)
    snapshots = sorted(work.glob("simulation_chip_*_mapped_fabric_shadow/native_lut_snapshot.json"))
    if len(snapshots) != 1:
        (out / "result.json").write_text(json.dumps({"status": "not_run", "snapshots": len(snapshots)}) + "\n")
        return
    snapshot = json.loads(snapshots[0].read_text())
    (out / "snapshot.json").write_text(json.dumps(snapshot, indent=2) + "\n")
    results = []
    for index, target in enumerate(snapshot["targets"]):
        module = target["module"]
        names = [module, target["output"], *target["configuration"]]
        if any(not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9.]*", name) for name in names):
            raise ValueError("Unexpected mapped signal name")
        if target["expected"] not in (0, 1) or any(v not in (0, 1) for v in target["configuration"].values()):
            raise ValueError("Non-binary proof constraint")
        netlist = work / f"fabulous-tiles/tiles/tiny/{module}/macro/ihp-sg13cmos5l/nl/{module}.nl.v"
        constraints = " ".join(f"-set {name} {value}" for name, value in target["configuration"].items())
        # Keep public aliases; do not optimize against the captured configuration.
        # No ignore_unknown_cells: unsupported logic must fail rather than vanish.
        script = "\n".join([
            f"read_liberty -ignore_miss_func {library}", f"read_verilog {netlist}",
            f"hierarchy -check -top {module}", "flatten", "proc",
            f"select -module {module}",
            "setattr -set keep 1 w:*ConfigMem* w:*.Q",
            "cutpoint t:$*ff* t:$*latch* t:$_DFF* t:$_DLATCH*",
            "opt_clean", f"write_json {out / f'target_{index}.json'}",
            # First establish feasibility, so an inconsistent constraint set
            # cannot masquerade as a successful constant-output proof.
            f"sat {constraints} -show {target['output']}",
            f"sat {constraints} -prove {target['output']} {target['expected']} -verify",
        ]) + "\n"
        path = out / f"target_{index}.ys"
        path.write_text(script)
        log_path = out / f"target_{index}.log"
        with log_path.open("w") as log:
            try:
                result = subprocess.run(["yosys", "-Q", "-T", "-s", str(path)],
                                        stdout=log, stderr=subprocess.STDOUT, timeout=60)
                code = result.returncode
            except subprocess.TimeoutExpired:
                code = "timeout"
        log = log_path.read_text()
        feasible = "SAT solving finished - model found:" in log
        proved = code == 0 and feasible and "SAT proof finished - no model found: SUCCESS!" in log
        results.append({"instance": target["instance"], "output": target["output"],
                        "expected": target["expected"], "configuration_bits": len(target["configuration"]),
                        "returncode": code, "feasible": feasible, "proved": proved})
    (out / "result.json").write_text(json.dumps({"scope": "combinational_binary_captured_configuration",
                                                "results": results}, indent=2) + "\n")

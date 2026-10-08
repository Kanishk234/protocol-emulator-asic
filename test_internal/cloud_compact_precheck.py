"""Package accepted driver geometry; run unmodified official TT precheck in cloud.

prepare only copies/hashes files. run exports a native top-block LEF and Verilog
from the authenticated final ODB and invokes the pinned official Nix toolchain.
Passing this diagnostic does not establish configured-fabric timing acceptance.
"""
import argparse
import hashlib
import json
import os
import re
from decimal import Decimal
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "build/cloud_driver_route_37708459393/clean_layout/fresh_streamout/final"
OUT = ROOT / "build/compact_precheck"
TOOLS = ROOT / "build/compact_precheck_tools"
SUPPORT = "d66cf179e7bc4d296362ab7e2e3b344dc3c4f665"
ACTION = "3412659307918422f3f0727917cf9b499aaca588"
IMAGE = "ghcr.io/librelane/librelane@sha256:d109140b8f17fc54f4fca998beb8124f4949404ec52e339eebd2250854a18b5a"
EXPECTED = {
    "tt_um_warp.gds": "bb415750feace175e140d2fbb3a9aca4b72731c248a884b46999eb933e3f3246",
    "source.odb": "b71f5f377faee63410781c4f108a7b9b06d26e2552ce9f3418b5f227fbf67285",
}
CHECKS = {"KLayout pin label overlapping drawing", "KLayout SG13CMOS5L DRC",
    "KLayout zero area", "KLayout Checks", "Pin check", "Boundary check",
    "Layer check", "Cell name check", "Analog pin check"}
EXPORT = r"""
read_db $::env(WARP_PRECHECK_ODB)
if {[[ord::get_db_block] getName] != "tt_um_warp"} {error "Unexpected top block"}
# write_lef emits the technology/library; native write_abstract_lef emits the
# top macro and preserves existing signal/power pin geometry and use types.
write_abstract_lef $::env(WARP_PRECHECK_LEF)
write_verilog -include_pwr_gnd $::env(WARP_PRECHECK_VERILOG)
"""


PUBLISH_GDS = r"""
import json, os
from pathlib import Path
import pya
layout = pya.Layout()
layout.read(os.environ["WARP_PRECHECK_SOURCE_GDS"])
top = layout.cell("tt_um_warp")
if top is None: raise RuntimeError("Missing authenticated chip top")
# Serialize only the actual chip and its complete referenced hierarchy.
# No referenced cell, label, polygon or instance may change.
def signature(cell, database):
    shapes = {str(database.get_info(layer)): sorted(shape.to_s() for shape in cell.shapes(layer).each())
              for layer in database.layer_indexes() if not cell.shapes(layer).is_empty()}
    instances = sorted((database.cell(inst.cell_index).name, inst.cplx_trans.to_s(),
                        str(inst.a), str(inst.b), inst.na, inst.nb) for inst in cell.each_inst())
    return {"shapes": shapes, "instances": instances}
reachable = {top.cell_index(), *top.called_cells()}
before = {layout.cell(index).name: signature(layout.cell(index), layout) for index in reachable}
options = pya.SaveLayoutOptions()
options.select_cell(top.cell_index())
layout.write(os.environ["WARP_PRECHECK_PUBLISHED_GDS"], options)
after_layout = pya.Layout()
after_layout.read(os.environ["WARP_PRECHECK_PUBLISHED_GDS"])
after_top = after_layout.top_cells()
if len(after_top) != 1 or after_top[0].name != "tt_um_warp":
    raise RuntimeError("Published GDS does not have exactly the chip top")
after = {cell.name: signature(cell, after_layout) for cell in after_layout.each_cell()}
# Pruning can renumber cell indices. Names/transforms/arrays and all shapes
# including labels must remain exactly identical at the same database units.
if layout.dbu != after_layout.dbu or before != after: raise RuntimeError("Referenced hierarchy or shapes changed")
Path(os.environ["WARP_PRECHECK_PUBLICATION_REPORT"]).write_text(json.dumps({
    "source_top_cells": sorted(cell.name for cell in layout.top_cells()),
    "published_top_cells": ["tt_um_warp"], "reachable_cells": len(before),
    "referenced_shapes_labels_instances_identical": True}, indent=2) + "\n")
"""


def fixed_point_lef(text):
    """Format geometric tokens to official fp3 syntax with exact value checks."""
    lines = []
    for line in text.splitlines(keepends=True):
        if re.match(r"^\s*(SIZE|ORIGIN|RECT|FOREIGN)\s", line):
            def number(match):
                value = Decimal(match.group())
                formatted = format(value, ".3f")
                if Decimal(formatted) != value:
                    raise RuntimeError("LEF geometry is not representable at official nanometer precision")
                return formatted
            # Foreign names are identifiers, never coordinate tokens.
            line = re.sub(r"(?<![\w.])[-+]?\d+(?:\.\d+)?(?![\w.])", number, line)
            # The official RECT parser expects single separators; native LEF
            # uses a double separator after RECT. Preserve numeric values.
            indent = line[:len(line) - len(line.lstrip())]
            ending = "\n" if line.endswith("\n") else ""
            line = indent + " ".join(line.strip().split()) + ending
        lines.append(line)
    return "".join(lines)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    bundle = ROOT / "build/compact_precheck_source"
    bundle.mkdir(exist_ok=False)
    # The accepted driver GDS is the strict same-layout overlay (raw merged
    # streamout has a different hash); authenticate the requested geometry.
    inputs = {"tt_um_warp.gds": SOURCE.parents[1] / "overlay/chip_trial.gds",
        "source.odb": SOURCE / "odb/tt_um_warp.odb",
        "source.nl.v": SOURCE / "nl/tt_um_warp.nl.v",
        "source.pnl.v": SOURCE / "pnl/tt_um_warp.pnl.v",
        "info.yaml": ROOT / "info.yaml", "LICENSE": ROOT / "LICENSE"}
    files = {}
    for name, path in inputs.items():
        if name in EXPECTED and sha(path) != EXPECTED[name]:
            raise RuntimeError(f"Wrong accepted driver source {name}")
        shutil.copyfile(path, bundle / name)
        files[name] = sha(bundle / name)
    (bundle / "ATTRIBUTION.md").write_text(
        "WARP experimental generated physical views, protocol-emulator-asic "
        "contributors, Apache-2.0 (LICENSE). Source GitHub run 37708459393. "
        "This archive is for strict official Tiny Tapeout precheck, not a "
        "submission or configured-fabric timing acceptance. Official tools "
        "and PDK are fetched separately under upstream licenses.\n")
    files["ATTRIBUTION.md"] = sha(bundle / "ATTRIBUTION.md")
    manifest = {"source_run": 37708459393, "source_stage": str(SOURCE.relative_to(ROOT)),
        "source_paths": {name: str(path.relative_to(ROOT)) for name, path in inputs.items()},
        "files": files, "official_support_commit": SUPPORT, "official_action_commit": ACTION}
    (bundle / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    archive = ROOT / "build/compact-precheck-source.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(bundle, arcname="source")
    print(json.dumps({"archive": str(archive), "sha256": sha(archive)}, indent=2))


def run(archive, expected):
    if sha(archive) != expected:
        raise RuntimeError("Source archive authentication failed")
    OUT.mkdir(exist_ok=False)
    with tarfile.open(archive) as tar:
        tar.extractall(OUT, filter="data")
    source = OUT / "source"
    manifest = json.loads((source / "manifest.json").read_text())
    for key, expected_hash in manifest["files"].items():
        path = (source / key).resolve()
        if not path.is_relative_to(source.resolve()) or sha(path) != expected_hash:
            raise RuntimeError(f"Changed/outside source file {key}")
    for key, expected_hash in EXPECTED.items():
        if sha(source / key) != expected_hash:
            raise RuntimeError(f"Not accepted driver source: {key}")
    if subprocess.check_output(["git", "-C", str(TOOLS), "rev-parse", "HEAD"],
            text=True).strip() != SUPPORT:
        raise RuntimeError("Official tools checkout differs")
    import yaml
    info = yaml.safe_load((source / "info.yaml").read_text())
    if info["project"]["top_module"] != "tt_um_warp" or info["project"]["tiles"] != "6x4":
        raise RuntimeError("Original project metadata contract differs")
    tcl = OUT / "export.tcl"
    tcl.write_text(EXPORT)
    command = ["docker", "run", "--rm", "-v", f"{ROOT}:{ROOT}", "-w", str(ROOT)]
    for key, path in {"ODB": source / "source.odb", "LEF": source / "tt_um_warp.lef",
            "VERILOG": source / "tt_um_warp.v"}.items():
        command += ["-e", f"WARP_PRECHECK_{key}={path}"]
    command += ["--entrypoint", "openroad", IMAGE, "-exit", str(tcl)]
    with (OUT / "native_export.log").open("w") as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=180, check=True)
    for name in ("tt_um_warp.lef", "tt_um_warp.v"):
        if not (source / name).is_file() or (source / name).stat().st_size == 0:
            raise RuntimeError(f"Missing native export {name}")
    published = OUT / "published"
    published.mkdir()
    shutil.copyfile(source / "info.yaml", published / "info.yaml")
    shutil.copyfile(source / "tt_um_warp.v", published / "tt_um_warp.v")
    (published / "tt_um_warp.lef").write_text(fixed_point_lef((source / "tt_um_warp.lef").read_text()))
    publish_script = OUT / "publish_gds.py"
    publish_script.write_text(PUBLISH_GDS)
    publication = {"SOURCE_GDS": source / "tt_um_warp.gds",
        "PUBLISHED_GDS": published / "tt_um_warp.gds",
        "PUBLICATION_REPORT": OUT / "publication.json"}
    command = ["docker", "run", "--rm", "-v", f"{ROOT}:{ROOT}", "-w", str(ROOT)]
    for key, path in publication.items(): command += ["-e", f"WARP_PRECHECK_{key}={path}"]
    command += [IMAGE, "klayout", "-b", "-r", str(publish_script)]
    with (OUT / "publication.log").open("w") as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=180, check=True)
    precheck = TOOLS / "precheck"
    (precheck / "reports").mkdir(exist_ok=True)
    invocation = shlex.join([sys.executable, "precheck.py", "--gds",
        str(published / "tt_um_warp.gds"), "--tech", "ihp-sg13cmos5l"])
    command = ["nix-shell", "--run", invocation]
    (OUT / "invocation.json").write_text(json.dumps({"command": command,
        "cwd": str(precheck), "PDK": os.environ["PDK"],
        "PDK_ROOT": os.environ["PDK_ROOT"], "support_commit": SUPPORT,
        "action_contract_commit": ACTION, "published_views_sha256": {
            name: sha(published / name) for name in ("tt_um_warp.gds", "tt_um_warp.lef", "tt_um_warp.v")}, "fresh_export_sha256": {
            name: sha(source / name) for name in ("tt_um_warp.lef", "tt_um_warp.v")}}, indent=2) + "\n")
    code = None
    try:
        with (OUT / "official_precheck.log").open("w") as log:
            code = subprocess.run(command, cwd=precheck, stdout=log,
                stderr=subprocess.STDOUT, timeout=2400).returncode
    finally:
        shutil.copytree(precheck / "reports", OUT / "reports", dirs_exist_ok=True)
    xml = OUT / "reports/results.xml"
    if not xml.is_file():
        raise RuntimeError(f"Official precheck did not emit XML: returncode={code}")
    cases = ET.parse(xml).getroot().findall(".//testcase")
    if len(cases) != len(CHECKS) or {case.get("name") for case in cases} != CHECKS:
        raise RuntimeError("Official precheck omitted or changed required IHP checks")
    errors = [case.get("name") for case in cases if any(case.find(tag) is not None
        for tag in ("error", "failure", "skipped"))]
    summary = {"source_archive_sha256": expected, "source_run": 37708459393,
        "returncode": code, "checks": sorted(CHECKS), "failed_or_skipped": errors,
        "strict_official_precheck_pass": code == 0 and not errors,
        "configured_fabric_timing_acceptance": False, "no_check_waivers": True}
    (OUT / "result.json").write_text(json.dumps(summary, indent=2) + "\n")
    for key, expected_hash in EXPECTED.items():
        if sha(source / key) != expected_hash:
            raise RuntimeError("Authenticated geometry/database mutated")
    if code != 0 or errors:
        raise RuntimeError(f"Strict official precheck failed: returncode={code}, checks={errors}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "run"))
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--sha256")
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    elif args.archive is None or args.sha256 is None or len(args.sha256) != 64:
        parser.error("run requires --archive and full SHA256")
    else:
        run(args.archive, args.sha256)

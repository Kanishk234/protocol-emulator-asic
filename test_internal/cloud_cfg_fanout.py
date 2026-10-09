"""Ten identity-buffer diagnostic on authenticated cluster8, without routing.

Original instances, all contracted signal connections and the fixed macro must
remain exact. Estimated STA is evidence only, never physical acceptance.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

from cloud_fanout_preflight import (IMAGE, EXPECTED, sha, transform, macro_contract)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/cfg_fanout"
INPUT = ROOT / "build/cfg_fanout_input"
SOURCE_SHA = "d32c6375fffb932ce77cce3da5df82dc3477c78e8ba7feed222fa10fb87db112"
DERIVED = {"odb": "0a0af0c1a0e4c413f52c43de70772dfff857a7c98402fa9b5b7e8dac19a53f99",
           "nl": "5bcc7ceb770d8f20fce68e43b90b8a23bdcb1aa05fc7e17f2672248bbc23c9fe",
           "sdc": "2fd4e213532d83ee258899b6fc1ed48c4e5d91ddb0ccbe21eea0226cc90fd56e"}
MASTER = "sg13cmos5l_buf_2"
PREFIX = "WARP_CFG_FANOUT_"

CENSUS = r"""
proc census {path} {
    set out [open $path w]
    set block [ord::get_db_block]
    foreach inst [$block getInsts] {
        puts $out "INST\t[$inst getName]\t[[$inst getMaster] getName]\t[$inst getOrigin]\t[$inst getOrient]\t[$inst getPlacementStatus]"
        foreach term [$inst getITerms] {
            set net [$term getNet]
            set name "NULL"
            if {$net != "NULL"} {set name [$net getName]}
            puts $out "PIN\t[$inst getName]/[[$term getMTerm] getName]\t[[$term getMTerm] getIoType]\t[[$term getMTerm] getSigType]\t$name"
        }
    }
    foreach term [$block getBTerms] {
        set net [$term getNet]
        set name "NULL"
        if {$net != "NULL"} {set name [$net getName]}
        puts $out "PORT\t[$term getName]\t[$term getIoType]\t[$term getSigType]\t$name"
    }
    close $out
}
"""

EDIT = r"""
read_db $::env(WARP_INPUT_ODB)
set block [ord::get_db_block]
census $::env(WARP_BEFORE)
set master [[ord::get_db] findMaster sg13cmos5l_buf_2]
if {$master == "NULL"} {error "Missing identity buffer master"}
set count 0
for {set col 1} {$col <= 5} {incr col} {
    set stem [expr {$col <= 2 ? "_05_" : "_04_"}]
    set expected [format {u_cfg.g_col[%d].u_col.%s} $col $stem]
    set source NULL
    foreach net [$block getNets] {
        if {[string map [list "\\" ""] [$net getName]] == $expected} {set source $net; break}
    }
    if {$source == "NULL" || [$source getSigType] != "SIGNAL"} {error "Missing exact target net $expected"}
    set loads {}; set drivers {}
    foreach term [$source getITerms] {
        set direction [[$term getMTerm] getIoType]
        if {$direction == "INPUT"} {
            lassign [[$term getInst] getOrigin] x y
            lappend loads [list $x $y [[$term getInst] getName] [[$term getMTerm] getName] $term]
        } elseif {$direction == "OUTPUT"} {lappend drivers $term} else {error "Unsupported target pin"}
    }
    set driver_stem [expr {$col <= 2 ? "_23_" : "_22_"}]
    set expected_driver [format {u_cfg.g_col[%d].u_col.%s} $col $driver_stem]
    if {[llength $loads] != 12 || [llength $drivers] != 1 || [llength [$source getBTerms]] != 0} {error "Target load/driver census changed"}
    set driver [lindex $drivers 0]
    if {[string map [list "\\" ""] [[$driver getInst] getName]] != $expected_driver || [[$driver getMTerm] getName] != "Y"} {error "Wrong target driver"}
    set loads [lsort -integer -index 0 $loads]
    for {set group 0} {$group < 2} {incr group} {
        set name WARP_CFG_FANOUT_${col}_${group}
        if {[$block findInst $name] != "NULL" || [$block findNet ${name}_net] != "NULL"} {error "Diagnostic already applied"}
        set inst [odb::dbInst_create $block $master $name]
        set branch [odb::dbNet_create $block ${name}_net]
        if {$inst == "NULL" || $branch == "NULL"} {error "Buffer insertion failed"}
        [$inst findITerm A] connect $source
        [$inst findITerm X] connect $branch
        foreach term [$inst getITerms] {
            set kind [[$term getMTerm] getSigType]
            if {$kind in {POWER GROUND}} {
                set rail [$block findNet [expr {$kind == "POWER" ? "VPWR" : "VGND"}]]
                if {$rail == "NULL"} {error "Missing original supply"}
                $term connect $rail
            }
        }
        set sx 0; set sy 0
        foreach row [lrange $loads [expr {6*$group}] [expr {6*$group+5}]] {
            lassign $row x y unused unused term
            incr sx $x; incr sy $y
            $term disconnect
            $term connect $branch
        }
        $inst setLocation [expr {$sx/6}] [expr {$sy/6}]
        $inst setPlacementStatus PLACED
        incr count
    }
}
if {$count != 10} {error "Incorrect added-buffer census"}
detailed_placement
check_placement -verbose
census $::env(WARP_AFTER)
write_db $::env(WARP_OUTPUT_ODB)
write_verilog $::env(WARP_OUTPUT_NL)
"""


def parse_census(text):
    instances, pins = {}, {}
    for line in text.splitlines():
        row = line.split("\t")
        if row[0] == "INST":
            if row[1] in instances: raise ValueError("Duplicate instance")
            instances[row[1]] = row[2:]
        elif row[0] in ("PIN", "PORT"):
            key = (row[0], row[1])
            if key in pins: raise ValueError("Duplicate terminal")
            pins[key] = row[2:]
        else: raise ValueError("Unsupported census row")
    return instances, pins


def verify_connections(before, after):
    """Contract exactly ten verified identity buffers; compare every old terminal."""
    old, oldpins = parse_census(before)
    new, newpins = parse_census(after)
    added = set(new) - set(old)
    expected = {f"{PREFIX}{col}_{group}" for col in range(1, 6) for group in range(2)}
    if added != expected or set(old) - set(new): raise ValueError("Unexpected added/removed instances")
    if any(new[name][0] != old[name][0] for name in old): raise ValueError("Original master changed")
    if "u_fabric" not in old or new.get("u_fabric") != old["u_fabric"] or old["u_fabric"][-1] != "FIRM":
        raise ValueError("Fixed macro moved/replaced or original placement status differs")
    parents = {}
    for name in sorted(added):
        if new[name][0] != MASTER: raise ValueError("Nonidentity added cell")
        terms = {key[1].rsplit("/", 1)[1]: value for key, value in newpins.items()
                 if key[0] == "PIN" and key[1].rsplit("/", 1)[0] == name}
        signal = {port: val for port, val in terms.items() if val[1] not in ("POWER", "GROUND")}
        if set(signal) != {"A", "X"} or signal["A"][:2] != ["INPUT", "SIGNAL"] or signal["X"][:2] != ["OUTPUT", "SIGNAL"]:
            raise ValueError("Unsupported buffer pins")
        input_net, output_net = signal["A"][2], signal["X"][2]
        if input_net == "NULL" or output_net == "NULL" or output_net in parents: raise ValueError("Invalid buffer connection")
        parents[output_net] = input_net
        for val in terms.values():
            if val[1] in ("POWER", "GROUND") and val[2] != ("VPWR" if val[1] == "POWER" else "VGND"):
                raise ValueError("Buffer supply changed")
        if sum(val[0] == "INPUT" and val[2] == output_net for val in newpins.values()) != 6:
            raise ValueError("Branch is not exactly six loads")
        if sum(val[0] == "OUTPUT" and val[2] == output_net for val in newpins.values()) != 1:
            raise ValueError("Branch has additional driver")
    for key, val in oldpins.items():
        peer = newpins.get(key)
        if not peer or peer[:2] != val[:2]: raise ValueError("Original terminal changed")
        net = peer[2]; seen = set()
        while net in parents:
            if net in seen: raise ValueError("Buffer feedback loop")
            seen.add(net); net = parents[net]
        if net != val[2]: raise ValueError("Original contracted connectivity changed: " + str(key))
    for key in set(newpins) - set(oldpins):
        if key[0] != "PIN" or key[1].rsplit("/", 1)[0] not in added:
            raise ValueError("Additional original terminal")
    displacement = []
    for name in old:
        oldxy, newxy = list(map(int, old[name][1].split())), list(map(int, new[name][1].split()))
        if len(oldxy) != 2 or len(newxy) != 2: raise ValueError("Invalid instance origin")
        displacement.append((abs(newxy[0] - oldxy[0]), abs(newxy[1] - oldxy[1])))
    return {"original_instances": len(old), "original_terminals": len(oldpins),
            "added_identity_buffers": len(added), "contracted_connectivity_exact": True,
            "fixed_macro_exact": True,
            "original_cells_moved": sum(dx != 0 or dy != 0 for dx, dy in displacement),
            "original_cell_max_manhattan_displacement_database_units": max(dx + dy for dx, dy in displacement),
            "original_cell_max_axis_displacement_database_units": max(max(dx, dy) for dx, dy in displacement)}


def single_corner_config(config, corner):
    """corner.tcl reports its first corner; run each original corner separately."""
    if corner not in config["STA_CORNERS"]: raise ValueError("Corner is not an original STA corner")
    selected = dict(config, PNR_CORNERS=[corner], DEFAULT_CORNER=corner)
    if any(selected[key] != value for key, value in config.items()
           if key not in {"PNR_CORNERS", "DEFAULT_CORNER"}):
        raise ValueError("Corner selection changed original inputs")
    return selected


def exact_corner_fanout(metrics, corner):
    prefix = "design__max_fanout_violation__count__corner:"
    counts = {key: value for key, value in metrics.items() if key.startswith(prefix)}
    if set(counts) != {prefix + corner}: raise ValueError("Missing/wrong actual STA corner metric")
    return counts


def run():
    OUT.mkdir(exist_ok=False)
    result = {"passed": False, "physical_or_timing_acceptance": False, "detailed_routing": False,
              "source_run": 37811985079, "original_max_fanout_constraint": 10,
              "original_reported_per_pin_fanout_limit": 8}
    def save(): (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    save()
    try:
        archive = ROOT / "build/fanout-preflight-source.tar.gz"
        if sha(archive) != SOURCE_SHA: raise ValueError("Source archive authentication failed")
        source_root = ROOT / "build/fanout_preflight"
        source_root.mkdir(exist_ok=False)
        with tarfile.open(archive) as tf: tf.extractall(source_root, filter="data")
        bundle = source_root / "fanout_source"
        manifest = json.loads((bundle / "manifest.json").read_text())
        if manifest["source_odb_sdc_nl"] != EXPECTED: raise ValueError("Wrong original pre-CTS inputs")
        for name, digest in manifest["files"].items():
            path = (bundle / name).resolve()
            if not path.is_relative_to(bundle.resolve()) or sha(path) != digest: raise ValueError("Changed bundle input")
        derived = INPUT / "cluster8/final"
        for kind, digest in DERIVED.items():
            path = derived / kind / ("tt_um_warp." + ("nl.v" if kind == "nl" else kind))
            if sha(path) != digest: raise ValueError("Changed cluster8 " + kind)
        result["derived_sha256"] = DERIVED
        config = transform(json.loads((bundle / "config.json").read_text()),
                           lambda text: text.replace("@BUNDLE@", str(bundle)).replace("@PDK@", os.environ["PDK_ROOT"]))
        if config.get("MAX_FANOUT_CONSTRAINT") != 10 or config["CLOCK_PERIOD"] != 20:
            raise ValueError("Original timing constraints differ")
        if config.get("PAD_LIBS") is None: config["PAD_LIBS"] = {}
        config["CTS_SINK_CLUSTERING_SIZE"] = 8
        # Pinned corner.tcl explicitly reports only the first defined corner.
        # Separate processes give real coverage of all original timing corners.
        corners = config["STA_CORNERS"]
        if len(corners) != 3 or len(set(corners)) != 3: raise ValueError("Expected exactly three original STA corners")
        result["measurement_corners"] = corners
        result["measurement_method"] = "six explicit single-corner STAMidPNR runs; identical ODB per design"
        config["meta"] = {"version": 2, "flow": ["OpenROAD.STAMidPNR"]}
        # Independently verify the chosen primitive's actual Liberty function.
        import re
        for paths in config["LIB"].values():
            std = next(Path(path) for path in paths if "stdcell" in path)
            text = std.read_text()
            match = re.search(r"cell\s*\(\s*" + MASTER + r"\s*\)\s*\{", text)
            if not match: raise ValueError("Buffer Liberty cell missing")
            end = re.search(r"\n\s*cell\s*\(", text[match.end():])
            section = text[match.end():match.end()+end.start()] if end else text[match.end():]
            if re.findall(r'function\s*:\s*"([^"]+)"', section) != ["A"]:
                raise ValueError("Buffer is not Liberty-proven identity")
        script = OUT / "buffer.tcl"
        script.write_text(CENSUS + EDIT)
        env = {"WARP_INPUT_ODB": derived / "odb/tt_um_warp.odb", "WARP_BEFORE": OUT / "before.tsv",
               "WARP_AFTER": OUT / "after.tsv", "WARP_OUTPUT_ODB": OUT / "buffered.odb",
               "WARP_OUTPUT_NL": OUT / "buffered.nl.v"}
        command = ["docker", "run", "--rm", "-v", f"{ROOT}:{ROOT}", "-w", str(ROOT)]
        for name, value in env.items(): command += ["-e", f"{name}={value}"]
        command += ["--entrypoint", "openroad", IMAGE, "-exit", str(script)]
        with (OUT / "buffer.log").open("w") as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
        result["connectivity"] = verify_connections((OUT / "before.tsv").read_text(), (OUT / "after.tsv").read_text())
        result["buffered_sha256"] = {kind: sha(Path(env[key])) for kind, key in
                                     (("odb", "WARP_OUTPUT_ODB"), ("nl", "WARP_OUTPUT_NL"))}
        (OUT / "config.json").write_text(json.dumps(config, indent=2) + "\n")
        save()
        def sta(label, odb, nl, corner):
            (OUT / label).mkdir(exist_ok=False)
            selected = single_corner_config(config, corner)
            config_path = OUT / (label + "_config.json")
            config_path.write_text(json.dumps(selected, indent=2) + "\n")
            state = {"odb": str(odb), "nl": str(nl), "sdc": str(derived / "sdc/tt_um_warp.sdc"), "metrics": {}}
            state_path = OUT / (label + "_state.json")
            state_path.write_text(json.dumps(state) + "\n")
            command = [sys.executable, "-m", "librelane", "--docker-no-tty", "--dockerized", "--pdk", "ihp-sg13cmos5l",
                   "--pdk-root", os.environ["PDK_ROOT"], "--manual-pdk", "--hide-progress-bar", "--force-run-dir", str(OUT / "sta"),
                   "--with-initial-state", str(state_path), str(config_path)]
            command[command.index("--force-run-dir") + 1] = str(OUT / label)
            with (OUT / (label + ".log")).open("w") as log:
                subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=300)
            stages = list((OUT / label).glob("*-openroad-stamidpnr"))
            if len(stages) != 1: raise ValueError("Missing unique completed estimated STA")
            resolved = json.loads((stages[0] / "config.json").read_text())
            if resolved["CELL_LIBS"] != config["LIB"] or macro_contract(resolved["MACROS"]) != macro_contract(config["MACROS"]):
                raise ValueError("STA changed library/macro inputs")
            for key in ("CLOCK_PORT", "CLOCK_PERIOD", "CLOCK_UNCERTAINTY_CONSTRAINT", "CLOCK_TRANSITION_CONSTRAINT",
                        "MAX_FANOUT_CONSTRAINT", "PNR_SDC_FILE", "FALLBACK_SDC", "PNR_CORNERS", "DEFAULT_CORNER"):
                if resolved.get(key) != selected.get(key): raise ValueError("STA changed constraint/corner " + key)
            metrics = json.loads((stages[0] / "state_out.json").read_text())["metrics"]
            counts = exact_corner_fanout(metrics, corner)
            result[label] = {"metrics": metrics, "fanout_corner_counts": counts, "corner": corner,
                             "odb_sha256": sha(Path(odb)), "sdc_sha256": sha(derived / "sdc/tt_um_warp.sdc")}
            save()
            return counts
        baseline = {}
        for corner in corners:
            baseline.update(sta("baseline_sta_" + corner, derived / "odb/tt_um_warp.odb", derived / "nl/tt_um_warp.nl.v", corner))
        if len(baseline) != 3: raise ValueError("Missing three independently measured baseline corners")
        if not all(value == 5 for value in baseline.values()): raise ValueError("Baseline fanout failure did not reproduce")
        fanout = {}
        for corner in corners:
            fanout.update(sta("buffered_sta_" + corner, env["WARP_OUTPUT_ODB"], env["WARP_OUTPUT_NL"], corner))
        if len(fanout) != 3: raise ValueError("Missing three independently measured candidate corners")
        result["baseline_fanout_corner_counts"] = baseline
        result["buffered_fanout_corner_counts"] = fanout
        for kind, digest in DERIVED.items():
            path = derived / kind / ("tt_um_warp." + ("nl.v" if kind == "nl" else kind))
            if sha(path) != digest: raise ValueError("Diagnostic mutated authenticated source " + kind)
        result["authenticated_sources_unchanged"] = True
        result["passed"] = all(value == 0 for value in fanout.values())
        if not result["passed"]: raise RuntimeError("Remaining actual max-fanout violations")
    except Exception as exc:
        result["error"] = str(exc)
        raise
    finally: save()


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    run()

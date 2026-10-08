"""Cloud-only C2 import/floorplan/pin preflight; no synthesis or signoff claim."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/tile_preflight"
INPUT = ROOT / "build/tile_preflight_input"
ARCHIVE_SHA = "d1d87cf442e6fbec1219edfbe243415f40e36fa0d9e07e5fc642ff19db33a64a"
IMAGE = "ghcr.io/librelane/librelane@sha256:d109140b8f17fc54f4fca998beb8124f4949404ec52e339eebd2250854a18b5a"
TOP = "LUT4x8_ha_C2"
PASSING_SHA = "03c21b8e400e1774390e67b0939422959d37e26849adca18fa082f492cf5cdaf"
ORIGINAL_SHA = "2c9faa6dc332004212c2719a8ca740b902d8c720f5f7da664007d3df7eedf6d9"
IO_SHA = "4517d4d40cfbadd7dfadc3d7415cd9ade794f3bbaefb21a5ce7bec9db4eefb32"
PIN_OBSERVER = r"""
read_db $::env(WARP_TILE_PIN_INPUT)
set block [ord::get_db_block]
set die [$block getDieArea]
puts "WARP_DIE\t[$die xMin]\t[$die yMin]\t[$die xMax]\t[$die yMax]"
foreach term [$block getBTerms] {
    if {[$term getSigType] in {POWER GROUND}} {continue}
    set boxes {}
    foreach pin [$term getBPins] {
        foreach box [$pin getBoxes] {
            lappend boxes "[[$box getTechLayer] getName],[$box xMin],[$box yMin],[$box xMax],[$box yMax]"
        }
    }
    if {![llength $boxes]} {error "Signal port has no geometry: [$term getName]"}
    puts "WARP_PIN\t[$term getName]\t[$term getIoType]\t[join [lsort $boxes] ;]"
}
"""


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_pin_inventory(text):
    dies, inventory = [], {}
    for line in text.splitlines():
        columns = line.split("\t")
        if columns[0] == "WARP_DIE":
            if len(columns) != 5:
                raise ValueError("Malformed native die census")
            dies.append(list(map(int, columns[1:])))
        elif columns[0] == "WARP_PIN":
            if len(columns) != 4 or columns[1] in inventory:
                raise ValueError("Malformed/duplicate native signal-pin census")
            boxes = []
            for encoded in columns[3].split(";"):
                layer, *rectangle = encoded.split(",")
                if len(rectangle) != 4 or not layer:
                    raise ValueError("Malformed signal-pin rectangle")
                boxes.append([layer, *map(int, rectangle)])
            inventory[columns[1]] = {"direction": columns[2], "boxes": sorted(boxes)}
    if len(dies) != 1 or not inventory:
        raise ValueError("Missing unique die/signal-pin inventory")
    return {"die": dies[0], "pins": inventory}


def unpack(archive):
    if sha(archive) != ARCHIVE_SHA:
        raise ValueError("Tile preflight archive hash mismatch")
    names = {"manifest.json", "original.nl.v", "passing.nl.v", "original_pins.odb",
             "original.lef", "original.def", "original.h.json", "original.sdc",
             "floorplan_config.json", "io_config.json", "pins.yaml", "io_place.py",
             "common.yaml", "tile.yaml", "LICENSE", "ATTRIBUTION.txt"}
    with tarfile.open(archive, "r:gz") as tf:
        members = tf.getmembers()
        if len(members) != len(names) or {x.name for x in members} != names:
            raise ValueError("Unexpected tile preflight archive members")
        if any(not x.isfile() or x.size > 20_000_000 for x in members):
            raise ValueError("Unsafe tile preflight archive member")
        INPUT.mkdir(exist_ok=False)
        for member in members:
            (INPUT / member.name).write_bytes(tf.extractfile(member).read())
    manifest = json.loads((INPUT / "manifest.json").read_text())
    if set(manifest["files"]) != names - {"manifest.json"}:
        raise ValueError("Incomplete tile preflight manifest")
    for name, digest in manifest["files"].items():
        if sha(INPUT / name) != digest:
            raise ValueError("Tile input hash mismatch: " + name)
    for name, digest in (("passing.nl.v", PASSING_SHA), ("original.nl.v", ORIGINAL_SHA),
                         ("io_place.py", IO_SHA)):
        if sha(INPUT / name) != digest:
            raise ValueError("Incorrect authenticated tile input: " + name)


def inner():
    # These imports execute only in the pinned EDA container on GitHub.
    from librelane.common import Path as LLPath
    from librelane.flows import SequentialFlow
    from librelane.state import State, DesignFormat
    from librelane.steps import OpenROAD, Odb

    class WarpTileIO(Odb.CustomIOPlacement):
        id = "Odb.WarpTileIO"

        def get_script_path(self):
            return str(INPUT / "io_place.py")

    class Preflight(SequentialFlow):
        Steps = [OpenROAD.Floorplan, Odb.SetPowerConnections, WarpTileIO]

    def pins(path):
        # OpenDB bindings live in OpenROAD's embedded interpreter, rather than
        # the container's ordinary Python. A native read-only Tcl observer
        # keeps that API boundary explicit and retains every signal rectangle.
        observer = OUT / "observe_pins.tcl"
        observer.write_text(PIN_OBSERVER)
        log = OUT / (path.parent.name + "_pins.log")
        with log.open("w") as stream:
            subprocess.run(["openroad", "-exit", str(observer)],
                           env=dict(os.environ, WARP_TILE_PIN_INPUT=str(path)),
                           stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=60)
        return parse_pin_inventory(log.read_text())

    result = {"scope": "C2 floorplan and signal-pin geometry only; no routing/PDN/timing/native acceptance",
              "passed": False, "synthesis_executed": False, "stages": {}}
    def save():
        (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    save()
    try:
        original_fp = json.loads((INPUT / "floorplan_config.json").read_text())
        original_io = json.loads((INPUT / "io_config.json").read_text())
        config = {key: original_fp[key] for key in (
            "DESIGN_NAME", "CLOCK_PERIOD", "CLOCK_PORT", "FP_SIZING", "DIE_AREA",
            "CORE_AREA", "BOTTOM_MARGIN_MULT", "TOP_MARGIN_MULT", "LEFT_MARGIN_MULT",
            "RIGHT_MARGIN_MULT", "VDD_NETS", "GND_NETS")}
        config.update({key: original_io[key] for key in (
            "IO_PIN_H_LAYER", "IO_PIN_V_LAYER", "IO_PIN_H_EXTENSION", "IO_PIN_V_EXTENSION",
            "IO_PIN_H_THICKNESS_MULT", "IO_PIN_V_THICKNESS_MULT", "IO_PIN_H_LENGTH", "IO_PIN_V_LENGTH")})
        config.update(IO_PIN_ORDER_CFG=str(INPUT / "pins.yaml"), ERRORS_ON_UNMATCHED_IO="both")
        reference = pins(INPUT / "original_pins.odb")
        (OUT / "reference_signal_pins.json").write_text(json.dumps(reference, indent=2) + "\n")
        pdk = Path(os.environ["PDK_ROOT"])
        liberty = pdk / "ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib/sg13cmos5l_stdcell_slow_1p08V_125C.lib"
        headers = []
        for name in ("original", "passing"):
            nl = INPUT / (name + ".nl.v")
            header = OUT / (name + ".h.json")
            with (OUT / (name + "_header.log")).open("w") as log:
                subprocess.run(["yosys", "-Q", "-T", "-p",
                    f"read_liberty -lib {liberty}; read_verilog {nl}; hierarchy -check -top {TOP}; write_json {header}"],
                    stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
            ports = json.loads(header.read_text())["modules"][TOP]["ports"]
            headers.append({port: (v["direction"], len(v["bits"])) for port, v in ports.items()})
            if len(headers) == 2 and headers[0] != headers[1]:
                raise ValueError("Candidate top-level ports differ from original")
            config["VERILOG_FILES"] = [str(nl)]
            flow = Preflight(config, design_dir=str(INPUT), pdk="ihp-sg13cmos5l", pdk_root=str(pdk))
            state = flow.start(with_initial_state=State({
                DesignFormat.NETLIST: LLPath(str(nl)), DesignFormat.JSON_HEADER: LLPath(str(header)),
                DesignFormat.SDC: LLPath(str(INPUT / "original.sdc"))}),
                _force_run_dir=str(OUT / name), tag=name)
            observed = pins(state[DesignFormat.ODB])
            (OUT / (name + "_signal_pins.json")).write_text(json.dumps(observed, indent=2) + "\n")
            result["stages"][name] = {"input_nl_sha256": sha(nl), "matches_original_pins": observed == reference,
                                     "signal_ports": len(observed["pins"]), "odb_sha256": sha(Path(state[DesignFormat.ODB]))}
            save()
            if observed != reference:
                raise ValueError(name + " pin geometry differs from authenticated original")
        result["passed"] = True
    except Exception as exc:
        result["error"] = str(exc)
        raise
    finally:
        save()


def main():
    if sys.argv[1:] == ["--inside-container"]:
        inner()
        return
    OUT.mkdir(exist_ok=False)
    archive = ROOT / "build/tile-preflight-c2.tar.gz"
    unpack(archive)
    command = ["docker", "run", "--rm", "-v", f"{ROOT}:{ROOT}", "-w", str(ROOT),
               "-e", "PDK_ROOT=" + os.environ["PDK_ROOT"], IMAGE,
               "python3", "test_internal/cloud_tile_preflight.py", "--inside-container"]
    with (OUT / "preflight.log").open("w") as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=600)


if __name__ == "__main__":
    main()

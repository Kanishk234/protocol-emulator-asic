#!/usr/bin/env python3
"""Simulate the complete compact candidate using the already compiled UART image."""

import argparse
import csv
import os
import sys
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from cocotb_tools.runner import get_runner

from prepare import DEFAULT_WORK, NAME, ROOT


def simulate(work: Path, words: Path, shell_netlist: Path | None = None,
             chip_dir: str = "chip", mapped_fabric: bool = False,
             settle_internal: bool = False, reset_probe: bool = False) -> None:
    work, words = work.resolve(), words.resolve()
    library = work / "fabulous-tiles"
    fabric_rtl = work / "macro/fabulous" / f"{NAME}.v"
    fabric = work / ("macro/nl" if mapped_fabric else "macro/fabulous") / (
        f"{NAME}.nl.v" if mapped_fabric else f"{NAME}.v")
    top = work / chip_dir / "tt_um_warp_candidate.v"
    if not words.is_file():
        raise FileNotFoundError(words)
    tiles = set()
    in_fabric = False
    for row in csv.reader((work / f"{NAME}.csv").open()):
        if row and row[0] == "FabricBegin":
            in_fabric = True
        elif row and row[0] == "FabricEnd":
            break
        elif in_fabric:
            tiles.update(name for name in row if name and name != "NULL")
    sim_name = "simulation" + ("" if chip_dir == "chip" else "_" + chip_dir)
    if mapped_fabric:
        sim_name += "_mapped_fabric"
    if settle_internal:
        if not mapped_fabric:
            raise ValueError("Internal routing settling is a mapped-fabric diagnostic")
        sim_name += "_internal_settle"
    if reset_probe:
        sim_name += "_reset_probe"
    shadow = mapped_fabric and os.environ.get("WARP_COMPACT_SHADOW_RTL") == "1"
    if shadow:
        sim_name += "_shadow"
    sim = work / (sim_name + ("_mapped_shell" if shell_netlist else ""))
    sim.mkdir(exist_ok=True)
    routing_nets = [m[1] for m in re.finditer(
        r"(?m)^\s*wire\s*(?:\[[^\]]*\])?\s*(Tile_X\d+Y\d+_\w+)\s*;",
        fabric_rtl.read_text(),
    ) if not m[1].split("_", 2)[2].startswith(("FrameData", "FrameStrobe"))]
    if mapped_fabric:
        # OpenROAD scalarizes vector wires into escaped identifiers. Select
        # only equivalents of the RTL harness's routing nets: never storage,
        # top-level ports or configuration buses introduced by synthesis.
        rtl_names = set(routing_nets)
        routing_nets = [name for name in re.findall(
            r"(?m)^\s*wire\s+(\\?Tile_X\d+Y\d+_\S+)\s*;", fabric.read_text()
        ) if name.lstrip("\\").split("[", 1)[0] in rtl_names]
    if not routing_nets:
        raise ValueError("No routing nets found for the D-023 settling harness")
    hierarchy = "user_project.u_fabric."
    refs = [hierarchy + net + (" " if net.startswith("\\") else "")
            for net in routing_nets]
    shadow_sources, shadow_instance = [], ""
    if shadow:
        sys.path.insert(0, str(ROOT / "test_internal"))
        from native_shadow import prepare_shadow
        shadow_sources, shadow_instance, shadow_refs = prepare_shadow(ROOT, library, fabric_rtl, tiles, sim)
        refs.extend(shadow_refs)
    if settle_internal:
        # Diagnostic only: include preserved intra-tile switch outputs in the
        # same D-023 pulse. Derive the allowlist from generated output ports;
        # exclude clock/reset/enable routes, all storage and all config buses.
        internal_count = 0
        for tile in sorted(tiles):
            tile_dir = library / "tiles/tiny" / tile
            matrix = tile_dir / f"{tile}_switch_matrix.v"
            if not matrix.is_file():
                continue
            outputs = set(re.findall(r"(?m)^\s*output\s+(\w+)\s*[,;]", matrix.read_text()))
            outputs = {name for name in outputs
                       if not name.startswith(("GCLK", "GSR", "GEN", "J_SR", "J_EN"))}
            netlist = (tile_dir / "macro/ihp-sg13cmos5l/nl" / f"{tile}.nl.v").read_text()
            names = [name for name in re.findall(r"(?m)^\s*wire\s+(\\\S+)\s*;", netlist)
                     if name.lstrip("\\").startswith(f"Inst_{tile}_switch_matrix.")
                     and name.rsplit(".", 1)[-1] in outputs]
            instances = re.findall(rf"(?m)^\s*{re.escape(tile)}\s+(Tile_X\d+Y\d+_\w+)\s*\(", fabric.read_text())
            for instance in instances:
                refs.extend(hierarchy + instance + "." + name + " " for name in names)
                internal_count += len(names)
        if not internal_count:
            raise ValueError("No preserved internal routing outputs found")
        print(f"Diagnostic internal routing pulse: {internal_count} additional data wires; "
              "no additional storage/config/clock forces")
    forces = "\n".join(f"  force {ref} = 'bx;" for ref in refs)
    zeros = "\n".join(f"  force {ref} = 'b0;" for ref in refs)
    releases = "\n".join(f"  release {ref};" for ref in refs)
    tb = sim / "tb.v"
    tb.write_text('''`timescale 1ns/1ps
module tb;
reg clk=0, rst_n=0, ena=0;
reg [7:0] ui_in=1, uio_in=0;
wire [7:0] uo_out, uio_out, uio_oe;
reg hold_x=0, settle_routing=0;
tt_um_warp user_project(.clk(clk), .rst_n(rst_n), .ena(ena),
  .ui_in(ui_in), .uo_out(uo_out), .uio_in(uio_in), .uio_out(uio_out), .uio_oe(uio_oe));
''' + shadow_instance + "always @(posedge hold_x) begin\n" + forces + "\nend\nalways @(negedge hold_x) begin\n" + releases +
        "\nend\nalways @(posedge settle_routing) begin\n" + zeros +
        "\n#1;\n" + releases + "\nend\nendmodule\n")
    sources = [shell_netlist.resolve() if shell_netlist else top, fabric, tb] + shadow_sources
    if not mapped_fabric:
        sources.append(library / "models_pack.v")
    build_args = ["-g2012"]
    if shell_netlist or mapped_fabric:
        # Same cell models and Icarus version as the template gate-level job.
        iv = Path.home() / ".cache/warp/iverilog-13/usr"
        if not (iv / "bin/iverilog").is_file():
            raise FileNotFoundError("Run scripts/gl_local.sh to provision Icarus 13")
        os.environ["PATH"] = str(iv / "bin") + os.pathsep + os.environ["PATH"]
        build_args += ["-DFUNCTIONAL", "-B" + str(iv / "lib/ivl")]
        refs = Path(os.environ.get("PDK_ROOT", str(Path.home() / ".cache/warp/pdk-full"))) / "ihp-sg13cmos5l/libs.ref"
        sources += [refs / "sg13cmos5l_stdcell/verilog/sg13cmos5l_stdcell.v",
                    refs / "sg13cmos5l_stdcell/verilog/sg13cmos5l_udp.v",
                    refs / "sg13cmos5l_io/verilog/sg13cmos5l_io.v"]
    if not shell_netlist:
        import json
        config = json.loads((work / chip_dir / "config.json").read_text())
        sources += [Path(path) for path in config["VERILOG_FILES"] if Path(path).resolve() != top.resolve()]
    for tile in sorted(tiles):
        if mapped_fabric:
            sources.append(library / "tiles/tiny" / tile / "macro/ihp-sg13cmos5l/nl" / f"{tile}.nl.v")
        else:
            sources += sorted((library / "tiles/tiny" / tile).glob("*.v"))
    if not mapped_fabric:
        for primitive in ("FABULOUS_LC", "IOBUF", "GBUF", "SYS_RESET"):
            sources.append(library / "primitives" / primitive / "fabulous" / f"{primitive}.v")
        sources += sorted((ROOT / "arch/prims").glob("*.v"))
    runner = get_runner("icarus")
    runner.build(sources=sources, hdl_toplevel="tb", build_dir=sim / "build",
                 build_args=build_args, log_file=sim / "build.log")
    runner.test(test_module="test_shell", hdl_toplevel="tb", test_dir=Path(__file__).parent,
                extra_env={"WARP_COMPACT_WORDS": str(words),
                           "WARP_COMPACT_RESET_PROBE": "1" if reset_probe else "0",
                           "WARP_COMPACT_SHARED_CRC": "1" if any(
                               path.name == "wp_crc32_shared_word.v" for path in sources) else "0"},
                results_xml=str(sim / "results.xml"), log_file=sim / "test.log")
    results = ET.parse(sim / "results.xml").getroot()
    cases = results.findall(".//testcase")
    if (len(cases) != 1 or any(results.findall(".//" + tag)
                              for tag in ("failure", "error", "skipped"))):
        raise RuntimeError(f"Simulation did not pass: {sim / 'results.xml'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--words", type=Path,
                        default=ROOT / "build/arch_explore/compiled_structural/uart_words.hex")
    parser.add_argument("--shell-netlist", type=Path,
                        help="Test mapped shell with RTL fabric (no SDF or macro timing)")
    parser.add_argument("--chip-dir", default="chip", help="Candidate wrapper subdirectory")
    parser.add_argument("--mapped-fabric", action="store_true",
                        help="Use hardened tile/macro standard-cell netlists (no SDF)")
    parser.add_argument("--settle-internal", action="store_true",
                        help="Diagnostic only: pulse preserved intra-tile data-routing outputs")
    parser.add_argument("--reset-probe", action="store_true",
                        help="Diagnostic only: send USER_RESET after RUN through the host interface")
    args = parser.parse_args()
    simulate(args.work, args.words, args.shell_netlist, args.chip_dir, args.mapped_fabric,
             args.settle_internal, args.reset_probe)

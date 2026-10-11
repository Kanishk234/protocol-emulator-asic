"""Prepare an authenticated configuration/clock audit; never execute STA.

Outputs describe actual storage pins and image-selected clock endpoints. They
are evidence for a reviewed timing diagnostic, not executable constraints or
timing acceptance. No circuit, model, image or existing SDC is modified.
"""
import argparse
import json
from pathlib import Path
import re

from cloud_native_stage import C2, sha, xml_status
from cloud_native_final_tile import FINAL_SHA, semantic_evidence
from compact_gate_probe import native_config_bindings

ROOT = Path(__file__).resolve().parents[1]
LOADED_RESULT_SHA = "05b1d75dc11d6329e537eb1e513e16bd381c3e883a31ee81807acc6accc0f73f"
WORDS_SHA = "363c84af0b5907dabd4c511e80db95987ca3b0e08ffb6bd5ca07fc601c7ba9ec"


def decode_image(words, rows):
    if rows < 1 or len(words) < 2 or words[0] != 0xFAB0FAB1 or words[-1] != 1 << 20:
        raise ValueError("Requires a complete framed image")
    if (len(words) - 2) % (rows + 1): raise ValueError("Incomplete image frame")
    decoded = {}
    for offset in range(1, len(words) - 1, rows + 1):
        header = words[offset]
        column, select = header >> 27, header & ((1 << 20) - 1)
        if not select or select & (select - 1): raise ValueError("Frame header is not one-hot")
        frame = select.bit_length() - 1
        for y in range(rows):
            key = (column, y, frame)
            if key in decoded: raise ValueError("Duplicate image frame")
            decoded[key] = words[offset + rows - y]
    return decoded


def audit_configuration_and_clocks(module, expected, x, y):
    bindings = native_config_bindings(module)
    if len(bindings) != 529 or len(set(bindings.values())) != 529:
        raise ValueError("C2 configuration inventory/binding uniqueness differs")
    configuration, values = [], {}
    for instance, (frame, bit) in sorted(bindings.items()):
        cell = module["cells"][instance]
        q = cell["connections"]["Q"]
        if len(q) != 1 or not isinstance(q[0], int) or q[0] in values:
            raise ValueError("Configuration Q must be unique live scalar")
        if (x, y, frame) not in expected: raise ValueError("Image omits required configuration frame")
        value = (expected[x, y, frame] >> bit) & 1
        values[q[0]] = value
        configuration.append({"instance": instance, "q_pin": instance + "/Q", "q_bit": q[0],
                              "frame": frame, "bit": bit, "image_value": value})
    drivers = {}
    for instance, cell in module["cells"].items():
        for port, direction in cell["port_directions"].items():
            if direction == "output":
                for bit in cell["connections"][port]:
                    if isinstance(bit, int): drivers.setdefault(bit, []).append((instance, cell, port))
    def driver(bit):
        found = drivers.get(bit, [])
        if len(found) != 1: raise ValueError("Clock/control has no unique driver")
        return found[0]
    def transparent_source(bit):
        seen = set(); chain = []
        while isinstance(bit, int):
            if bit in seen: raise ValueError("Clock buffer loop")
            seen.add(bit)
            found = drivers.get(bit, [])
            if len(found) != 1: break
            instance, cell, port = found[0]
            if not cell["type"].startswith(("sg13cmos5l_buf_", "sg13cmos5l_dlygate")): break
            if port != "X" or len(cell["connections"]["A"]) != 1: raise ValueError("Unsupported clock buffer")
            chain.append(instance); bit = cell["connections"]["A"][0]
        return bit, chain
    flops = {name: cell for name, cell in module["cells"].items() if cell["type"] == "sg13cmos5l_dfrbpq_1"}
    if len(flops) != 8: raise ValueError("C2 user FF inventory differs")
    endpoints = []
    for instance, cell in sorted(flops.items()):
        if any(len(cell["connections"][port]) != 1 for port in ("D", "Q", "CLK", "RESET_B")):
            raise ValueError("User storage pins must be scalar")
        clock_bit, buffers = transparent_source(cell["connections"]["CLK"][0])
        mux_name, mux, mux_port = driver(clock_bit)
        if mux["type"] != "sg13cmos5l_mux4_1" or mux_port != "X": raise ValueError("User clock is not the proven mux4 path")
        controls = []; control_bindings = []
        for selector in ("S0", "S1"):
            bit, unused = transparent_source(mux["connections"][selector][0])
            if bit not in values: raise ValueError("Clock selector is not audited configuration Q")
            controls.append(values[bit])
            control_bindings.append(next(record for record in configuration if record["q_bit"] == bit))
        selected = controls[0] + 2 * controls[1]
        source_bit, source_buffers = transparent_source(mux["connections"]["A" + str(selected)][0])
        sources = [(name, index) for name, port in module["ports"].items() if port["direction"] == "input"
                   for index, bit in enumerate(port["bits"]) if bit == source_bit]
        if sources != [("N_GBUF_END", 3)]: raise ValueError("Loaded user clock does not select N_GBUF_END[3]")
        reset = cell["connections"]["RESET_B"][0]
        if reset != "1":
            reset_name, reset_cell, reset_port = driver(reset)
            if reset_cell["type"] != "sg13cmos5l_tiehi" or reset_port != "L_HI":
                raise ValueError("Async FF reset is not actual tie-high")
        endpoints.append({"instance": instance, "clock_pin": instance + "/CLK", "clock_bit": cell["connections"]["CLK"][0],
                          "clock_mux": mux_name, "selector_values_s0_s1": controls,
                          "clock_selector_configuration_s0_s1": control_bindings,
                          "clock_boundary_port": "N_GBUF_END[3]", "clock_buffers": source_buffers + buffers,
                          "d_pin": instance + "/D", "q_pin": instance + "/Q", "reset_b_pin": instance + "/RESET_B",
                          "reset_b_tie_high": True, "data_reset_paths_must_remain_dynamic": True})
    return {"tile_position": [x, y], "configuration_count": len(configuration), "configuration": configuration,
            "user_ff_count": len(endpoints), "user_clock_endpoints": endpoints}


def prepare(native, physical, words_path, out):
    result_path = native / "result.json"
    if sha(result_path) != LOADED_RESULT_SHA: raise ValueError("Loaded functional evidence identity differs")
    recorded = json.loads(result_path.read_text())
    if recorded["passed"] is not True or recorded["source_final_c2_sha256"] != FINAL_SHA:
        raise ValueError("Actual final C2 did not pass loaded test")
    if sha(words_path) != WORDS_SHA or WORDS_SHA not in recorded["simulation_sources"].values():
        raise ValueError("Loaded image identity differs")
    final = physical / "last_completed/nl" / (C2 + ".nl.v")
    if sha(final) != FINAL_SHA or sha(native / "source_final_c2.nl.v") != FINAL_SHA:
        raise ValueError("Physical/functional final netlist mismatch")
    for stage in ("passing_original_control", "hardened_final_c2"):
        for case in ("native_loaded", "native_user_reset"):
            directory = native / stage / case
            if not xml_status(directory / "results.xml")["passed"] or not all(
                    semantic_evidence((directory / "test.log").read_text(), case == "native_user_reset").values()):
                raise ValueError("Loaded interface/configuration/stress evidence incomplete")
    cone = native / "hardened_final_c2/matched_native_cone.json"
    if sha(cone) != recorded["stages"]["hardened_final_c2"]["matched_cone_sha256"]:
        raise ValueError("Matched cone identity differs")
    graph = json.loads(cone.read_text())
    proof = graph["warp_native_input_provenance"][C2]
    if proof["sha256"] != FINAL_SHA: raise ValueError("Matched cone has different physical C2")
    modules = graph["modules"]
    macros = [module for module in modules.values() if "Tile_X2Y3_" + C2 in module.get("cells", {})]
    if len(macros) != 1: raise ValueError("No unique actual fabric hierarchy")
    macro = macros[0]
    rows = 1 + max(int(re.match(r"Tile_X\d+Y(\d+)_", name)[1]) for name in macro["cells"] if name.startswith("Tile_X"))
    expected = decode_image([int(word, 16) for word in words_path.read_text().split()], rows)
    audits = [audit_configuration_and_clocks(modules[C2], expected, 2, y) for y in (1, 3)]
    physical_views = {}
    for relative in ("odb/LUT4x8_ha_C2.odb", "lef/LUT4x8_ha_C2.lef", "gds/LUT4x8_ha_C2.gds",
                     "nl/LUT4x8_ha_C2.nl.v", "spef/nom/LUT4x8_ha_C2.nom.spef", "sdc/LUT4x8_ha_C2.sdc"):
        path = physical / "last_completed" / relative
        physical_views[relative] = sha(path)
    spef = (physical / "last_completed/spef/nom/LUT4x8_ha_C2.nom.spef").read_text()
    if '*DESIGN "LUT4x8_ha_C2"' not in spef: raise ValueError("SPEF design identity differs")
    out.mkdir(parents=True, exist_ok=False)
    audit = {"preparation_completed": True, "sta_executed": False, "timing_pass_claimed": False,
             "models_or_constraints_modified": False, "state_forced": False,
             "source_runs": {"physical": 37814078650, "loaded_functional": 37958116481},
             "loaded_result_sha256": LOADED_RESULT_SHA, "image_sha256": WORDS_SHA,
             "matched_cone_sha256": sha(cone), "physical_view_sha256": physical_views,
             "source_hardening_outcome": json.loads((physical / "result.json").read_text()),
             "tile_instance_audits": audits,
             "remaining_gates": ["Review diagnostic clock/I/O boundary policy before any SDC generation",
                "Pin runner OpenSTA version and validate command/clock/annotation coverage",
                "Prove configuration stability/FrameStrobe idle in RUN mode",
                "Preserve all eight real user clocks and dynamic user-reset D paths",
                "Report configured loops/unconstrained endpoints without silently cutting them",
                "Separate loader electrical/setup/hold checks from static RUN case analysis",
                "Full-fabric signoff needs matching physical views and intertile/shell parasitics"]}
    (out / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps({"audit": str(out / "audit.json"), "sta_executed": False,
                      "configuration_values": 1058, "clock_endpoints": 16}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-evidence", type=Path, required=True)
    parser.add_argument("--physical-evidence", type=Path, required=True)
    parser.add_argument("--words", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=ROOT / "build/configured_c2_timing_audit")
    args = parser.parse_args()
    prepare(args.native_evidence, args.physical_evidence, args.words, args.out)

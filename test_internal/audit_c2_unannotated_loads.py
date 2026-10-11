"""Authenticate and audit fanout of actual C2 unannotated drivers, read-only."""
import argparse
import hashlib
import json
from pathlib import Path

GRAPH_SHA = "313a7c727a0105813daef7b12efa1b52b921663905089cc902a2450d882fb5a4"
NL_SHA = "a986a0864ab51f09f6157422ba7dff935585b6456e6accc7b64ac8228725e882"
DRIVERS = ["N2END[1]", "S2END[5]", "W2END[3]", "TIE_ZERO_zero_/L_LO"]


def audit(graph_path, reports):
    if hashlib.sha256(graph_path.read_bytes()).hexdigest() != GRAPH_SHA:
        raise ValueError("Actual loaded candidate graph differs")
    graph = json.loads(graph_path.read_text())
    if graph["warp_native_input_provenance"]["LUT4x8_ha_C2"]["sha256"] != NL_SHA:
        raise ValueError("Graph mapped source differs")
    module = graph["modules"]["LUT4x8_ha_C2"]
    rows = []
    for driver in DRIVERS:
        if "/" in driver:
            name, pin = driver.split("/")
            cell = module["cells"][name]
            if cell["port_directions"][pin] != "output":
                raise ValueError("Expected output driver")
            bits = cell["connections"][pin]
        else:
            name, index = driver.rstrip("]").split("[")
            port = module["ports"][name]
            if port["direction"] != "input" or port.get("offset", 0) != 0:
                raise ValueError("Unexpected port direction/indexing")
            bits = [port["bits"][int(index)]]
        if len(bits) != 1 or not isinstance(bits[0], int):
            raise ValueError("Driver bit is not one actual signal")
        bit = bits[0]
        loads = []
        for name, cell in module["cells"].items():
            for pin, connected in cell["connections"].items():
                if cell["port_directions"][pin] in ("input", "inout") and bit in connected:
                    loads.append(name + "/" + pin)
        outputs = [name for name, port in module["ports"].items()
                   if port["direction"] in ("output", "inout") and bit in port["bits"]]
        if loads or outputs:
            raise ValueError("Unannotated driver has real loads: " + driver)
        rows.append({"driver": driver, "graph_bit": bit, "cell_loads": loads,
                     "output_ports": outputs})
    hashes = {}
    for path in reports:
        expected = ["Found 4 unannotated drivers."] + [" " + d for d in DRIVERS] + ["Found 0 partially unannotated drivers."]
        if path.read_text().splitlines() != expected:
            raise ValueError("Native annotation report scope differs")
        hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    if len(hashes) != 6:
        raise ValueError("Expected all six actual annotation reports")
    return {"graph_sha256": GRAPH_SHA, "mapped_netlist_sha256": NL_SHA,
            "annotation_reports_sha256": hashes, "drivers": rows,
            "scope": "Four reported drivers have no loads in this exact tile graph; no full-chip timing acceptance"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph", type=Path)
    parser.add_argument("reports", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.graph, sorted(args.reports.glob("X2Y*/*/annotation.rpt"))), indent=2))

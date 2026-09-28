"""Report direct standard-cell areas without double-counting hierarchy."""
import argparse
import json
import re
from decimal import Decimal
from pathlib import Path

def report(work: Path) -> dict:
    liberty = (work / "cells.lib").read_text()
    headers = list(re.finditer(r'\bcell\s*\(\s*"?([^"\s)]+)"?\s*\)\s*\{', liberty))
    areas = {}
    for i, match in enumerate(headers):
        block = liberty[match.end():headers[i+1].start() if i+1<len(headers) else len(liberty)]
        area = re.search(r'\barea\s*:\s*([0-9.eE+-]+)\s*;', block)
        if area is None:
            raise ValueError(f"Missing cell area: {match[1]}")
        areas[match[1]] = Decimal(area[1])
    if not areas:
        raise ValueError("No Liberty cell areas found")
    result = {}
    for name in ("word", "byte"):
        net = json.loads((work / f"{name}-net.json").read_text())["modules"]
        boundary = net["wp_loader_boundary"]
        assert int(boundary["attributes"]["blackbox"],2)==1 and not boundary["cells"]
        top, loader = net["reference_validated_top"], net["eFPGA_top"]
        assert sum(c["type"]=="eFPGA_top" for c in top["cells"].values())==1
        assert sum(c["type"]=="wp_loader_boundary" for c in loader["cells"].values())==1
        bits = loader["netnames"]["FrameRegister"]["bits"]
        assert len(bits)==448 and len(set(bits))==448 and all(isinstance(b,int) for b in bits)
        stats = json.loads((work / f"{name}-area.json").read_text())["modules"]
        blocks, total = {}, Decimal(0)
        for module, child in (("reference_validated_top","eFPGA_top"),("eFPGA_top","wp_loader_boundary")):
            cells = stats["\\"+module]["num_cells_by_type"]
            assert cells.get(child)==1
            assert all(c.startswith("sg13cmos5l_") or c in (child,"$scopeinfo") for c in cells)
            direct = {c:n for c,n in cells.items() if c.startswith("sg13cmos5l_")}
            area = sum((areas[c]*n for c,n in direct.items()), Decimal(0))
            blocks[module] = {"cells":sum(direct.values()),"direct_area_um2":float(area)}
            total += area
        # Yosys module area includes child modules: sum direct areas exactly once.
        hierarchical = Decimal(str(stats["\\reference_validated_top"]["area"]))
        assert abs(total-hierarchical) < Decimal("0.001"), (name,total,hierarchical)
        result[name] = {"blocks":blocks,
                        "total_cells":sum(b["cells"] for b in blocks.values()),
                        "total_area_um2":float(total), "yosys_hierarchical_area_um2":float(hierarchical),
                        "observable_row_bits":448,"excluded_fabric_boundaries":1}
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path)
    args = parser.parse_args()
    result = report(args.work)
    (args.work / "summary.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))

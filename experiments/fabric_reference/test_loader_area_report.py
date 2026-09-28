import json
from pathlib import Path

import pytest

from loader_area_report import report


def fixture_files(tmp_path: Path) -> Path:
    # One wrapper instance contains one loader. Yosys area is recursive,
    # while each cell histogram is local to its module.
    (tmp_path / "cells.lib").write_text(
        'library(test) { cell(sg13cmos5l_and) { area: 2; } '
        'cell(sg13cmos5l_ff) { area: 3; } }')
    modules = {
        "wp_loader_boundary": {"attributes": {"blackbox": "1"}, "cells": {}},
        "reference_validated_top": {"cells": {"loader": {"type": "eFPGA_top"}}},
        "eFPGA_top": {
            "cells": {"fabric": {"type": "wp_loader_boundary"}},
            "netnames": {"FrameRegister": {"bits": list(range(2, 450))}},
        },
    }
    stats = {"modules": {
        "\\reference_validated_top": {"area": 13, "num_cells_by_type": {
            "eFPGA_top": 1, "sg13cmos5l_and": 2}},
        "\\eFPGA_top": {"area": 9, "num_cells_by_type": {
            "wp_loader_boundary": 1, "sg13cmos5l_ff": 3}},
    }}
    for name in ("word", "byte"):
        (tmp_path / f"{name}-net.json").write_text(json.dumps({"modules": modules}))
        (tmp_path / f"{name}-area.json").write_text(json.dumps(stats))
    return tmp_path


def test_hierarchical_area_counted_once(tmp_path):
    result = report(fixture_files(tmp_path))
    for variant in result.values():
        assert variant["total_area_um2"] == 13  # Not recursive 13 + child 9.
        assert variant["total_cells"] == 5
        assert variant["blocks"]["reference_validated_top"]["direct_area_um2"] == 4


def test_rejects_inconsistent_total(tmp_path):
    work = fixture_files(tmp_path)
    path = work / "word-area.json"
    stats = json.loads(path.read_text())
    stats["modules"]["\\reference_validated_top"]["area"] = 22
    path.write_text(json.dumps(stats))
    with pytest.raises(AssertionError):
        report(work)


def test_rejects_pruned_row_bit(tmp_path):
    work = fixture_files(tmp_path)
    path = work / "byte-net.json"
    net = json.loads(path.read_text())
    net["modules"]["eFPGA_top"]["netnames"]["FrameRegister"]["bits"][0] = "0"
    path.write_text(json.dumps(net))
    with pytest.raises(AssertionError):
        report(work)

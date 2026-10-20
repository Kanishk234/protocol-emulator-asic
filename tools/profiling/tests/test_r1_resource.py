from collections import Counter
import csv
import importlib.util
import io
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'spikes/r1'))
spec=importlib.util.spec_from_file_location('r1_resource',ROOT/'spikes/r1/resource_control.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_resource_control_expands_only_grid():
    before=(ROOT/'arch/warp_g1/fabric.csv').read_text()
    after=m.expanded_csv(before)
    rows=list(csv.reader(io.StringIO(after)))
    start=next(i for i,r in enumerate(rows) if r and r[0]=='FabricBegin')
    end=next(i for i,r in enumerate(rows) if r and r[0]=='FabricEnd')
    grid=rows[start+1:end]
    assert len(grid)==5 and all(len(row)==8 for row in grid)
    counts=Counter(t for row in grid for t in row)
    assert counts['LUT4x8_ha']==16 and counts['PRIM2T2S']==2
    assert after.split('FabricEnd',1)[1]==before.split('FabricEnd',1)[1]


def test_wrong_control_rejected():
    with pytest.raises(ValueError):
        m.expanded_csv((ROOT/'arch/warp_g1/fabric.csv').read_text().replace('LUT4x8_ha','WRONG'))

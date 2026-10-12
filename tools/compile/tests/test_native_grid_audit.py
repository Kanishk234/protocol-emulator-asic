"""Independent malformed-report and missing-guide guards for native routing."""
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/"test_internal"))
from audit_native_grid import audit,guide_coverage


def grid():
    return "META\t2\t2\nX\t0 10\nY\t0 10\n" + "".join(
        f"CELL\tMetal{i}\t0\t0\t2\t{3 if i==2 else 1}\n" for i in range(1,5))


def test_actual_overflow_arithmetic(tmp_path):
    p=tmp_path/"grid";p.write_text(grid());r=audit(p)
    assert r["total_overflow"]==1 and r["layers"]["Metal2"]["overflow"]==1
    assert r["observed_cells"]==4


@pytest.mark.parametrize("mutation",["duplicate","missing","nan","negative","axis","bounds","layer"])
def test_malformed_or_incomplete_grid_rejected(tmp_path,mutation):
    text=grid()
    if mutation=="duplicate":text+=text.splitlines()[-1]+"\n"
    elif mutation=="missing":text="\n".join(text.splitlines()[:-1])+"\n"
    elif mutation=="nan":text=text.replace("\t2\t1","\tNaN\t1",1)
    elif mutation=="negative":text=text.replace("\t2\t1","\t2\t-1",1)
    elif mutation=="axis":text=text.replace("X\t0 10","X\t10 0")
    elif mutation=="bounds":text=text.replace("Metal1\t0\t0","Metal1\t1\t0")
    elif mutation=="layer":text=text.replace("Metal1","Metal5")
    p=tmp_path/"grid";p.write_text(text)
    with pytest.raises(ValueError):audit(p)


CENSUS="INST\tcell\tbuf\t0 0\tR0\tPLACED\nPIN\tcell/A\tINPUT\tSIGNAL\tnet\nPORT\tinput\tINPUT\tSIGNAL\tnet\n"


def test_missing_guides_are_explicit(tmp_path):
    p=tmp_path/"guides";p.write_text("NET\tnet\t2\t0\t0\n")
    assert guide_coverage(p,CENSUS)["missing_guides"]==["net"]
    p.write_text("NET\tnet\t2\t1\t0\n")
    assert not guide_coverage(p,CENSUS)["missing_guides"]


def test_guide_inventory_must_match_native_connectivity(tmp_path):
    p=tmp_path/"guides";p.write_text("NET\tnet\t1\t1\t0\n")
    with pytest.raises(ValueError):guide_coverage(p,CENSUS)

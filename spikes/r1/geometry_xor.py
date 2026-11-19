"""KLayout batch geometry comparison with an in-memory added-metal control."""
import hashlib
import json
from pathlib import Path


def compare(reference,candidate,top_name,out):
    import pya
    before=pya.Layout();before.read(str(reference));after=pya.Layout();after.read(str(candidate))
    a,b=before.cell(top_name),after.cell(top_name)
    if a is None or b is None or before.dbu!=0.001 or after.dbu!=0.001:
        raise ValueError('Missing named macro or wrong geometry DBU')
    def layers(layout):
        return {(layout.get_info(i).layer,layout.get_info(i).datatype):i for i in layout.layer_indices()}
    la,lb=layers(before),layers(after);rows=[];negative=False
    for key in sorted(set(la)|set(lb)):
        ra=pya.Region(a.begin_shapes_rec(la[key])) if key in la else pya.Region()
        rb=pya.Region(b.begin_shapes_rec(lb[key])) if key in lb else pya.Region()
        diff=ra^rb
        rows.append(dict(layer=key[0],datatype=key[1],different=not diff.is_empty(),
                         difference_polygons=diff.count(),difference_area_dbu2=diff.area()))
        if key==(10,0):
            # Only a calibration region in memory; no source/output GDS changes.
            altered=rb+pya.Region(pya.Box(-10000,-10000,-9900,-9900))
            negative=not (ra^altered).is_empty()
    result=dict(passed=bool(rows) and not any(r['different'] for r in rows) and negative,
                layers_compared=len(rows),layers_with_differences=sum(r['different'] for r in rows),
                negative_control_detected=negative,layers=rows,ignored_geometry_layers=[],
                reference_sha256=hashlib.sha256(Path(reference).read_bytes()).hexdigest(),
                candidate_sha256=hashlib.sha256(Path(candidate).read_bytes()).hexdigest(),
                scope='All polygon/path/box geometry in the named macro hierarchy at1nmDBU; text/port metadata and electrical/timing acceptance are separate.')
    Path(out).write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    # KLayout supplies -rd variables as globals in its embedded Python runner.
    result=compare(reference,candidate,top_name,out)  # noqa: F821
    if not result['passed']:raise SystemExit('Flat route geometry/XOR control failed')

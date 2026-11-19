"""KLayout batch geometry comparison with an in-memory added-metal control."""
import hashlib
import json
from pathlib import Path


def restore_pin_markers(reference,candidate,top_name,allowed_boxes,out):
    import pya
    before=pya.Layout();before.read(str(reference));after=pya.Layout();after.read(str(candidate))
    a,b=before.cell(top_name),after.cell(top_name)
    if a is None or b is None or before.dbu!=0.001 or after.dbu!=0.001:
        raise ValueError('Missing macro or wrong marker geometry DBU')
    def layers(layout):
        return {(layout.get_info(i).layer,layout.get_info(i).datatype):i for i in layout.layer_indices()}
    la,lb=layers(before),layers(after);allowed={k:pya.Region() for k in [(10,2),(30,2)]};restored=[]
    for row in json.loads(Path(allowed_boxes).read_text()):
        key=(row['layer'],row['datatype'])
        if key not in allowed:raise ValueError('Unreviewed pin-marker purpose')
        allowed[key].insert(pya.Box(*row['box_dbu']))
    for key in sorted(set(la)|set(lb)):
        ra=pya.Region(a.begin_shapes_rec(la[key])).merged() if key in la else pya.Region()
        rb=pya.Region(b.begin_shapes_rec(lb[key])).merged() if key in lb else pya.Region()
        missing=(ra-rb).merged();extra=(rb-ra).merged()
        if missing.is_empty() and extra.is_empty():continue
        if key not in allowed or not extra.is_empty() or not (missing-allowed[key]).merged().is_empty():
            raise ValueError('Geometry change is not missing source-proven pin metadata: '+str(key))
        b.shapes(after.layer(*key)).insert(missing)
        restored.append(dict(layer=key[0],datatype=key[1],polygons=missing.count(),area_dbu2=missing.area()))
    after.write(str(out))
    return dict(restored_markers=restored,source_boxes_sha256=hashlib.sha256(Path(allowed_boxes).read_bytes()).hexdigest(),
                ignored_geometry_layers=[],scope='Only missing Metal2.pin/Metal3.pin geometry inside original final-ODB pin boxes is copied; all other changes are rejected.')


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
    restoration=None
    if 'allowed_boxes' in globals():
        restored=str(Path(out).with_suffix('.restored.gds'))  # noqa: F821
        restoration=restore_pin_markers(reference,candidate,top_name,allowed_boxes,restored)  # noqa: F821
        candidate=restored
    result=compare(reference,candidate,top_name,out)  # noqa: F821
    if restoration is not None:
        result['pin_marker_restoration']=restoration
        Path(out).write_text(json.dumps(result,indent=2)+'\n')  # noqa: F821
    if not result['passed']:raise SystemExit('Flat route geometry/XOR control failed')

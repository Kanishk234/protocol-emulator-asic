"""D-052 scratch geometry overlay; never modify the pinned IHP library.

Source: IHP-Open-PDK 2bbec755dc67ca3db0261c3d6163e15735d66710,
sg13cmos5l_stdcell (Apache-2.0; upstream license retained in fetched PDK).
This diagnostic is not a qualified replacement library.
"""
import pya


def clone_trial(layout, source, width):
    clone = layout.create_cell("wp_" + source.name + "_psd_trial")
    clone.copy_tree(source)
    unit = layout.dbu
    psd = layout.layer(14, 0)
    before = {layer: pya.Region(source.begin_shapes_rec(layer)).merged()
              for layer in layout.layer_indexes()}
    # Extend the existing ground-side pSD stripe 0.30um inward. Contacts,
    # diffusion, metals, pins and nominal footprint remain identical.
    clone.shapes(psd).insert(pya.Box(round(-0.07 / unit), round(0.18 / unit),
                                   round((width + 0.07) / unit), round(0.48 / unit)))
    for layer, region in before.items():
        after = pya.Region(clone.begin_shapes_rec(layer)).merged()
        if layer != psd and not (region ^ after).is_empty():
            raise RuntimeError("Trial changed a non-pSD layer")
    if clone.bbox() != source.bbox():
        raise RuntimeError("Trial changed the cell bounding box")
    added = pya.Region(clone.begin_shapes_rec(psd)) - before[psd]
    return clone, {"source": source.name, "trial": clone.name,
                   "nominal_width_um": width, "nominal_height_um": 3.78,
                   "added_psd_area_um2": added.area() * unit * unit,
                   "other_layers_identical": True, "bbox_identical": True}

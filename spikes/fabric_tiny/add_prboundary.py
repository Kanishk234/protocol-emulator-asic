# KLayout batch script: add the IHP placement boundary (prBoundary.boundary, GDS 189/4) over the
# whole top cell of a KLayout-written macro GDS. LibreLane's Magic stream-out of the chip needs it
# to find the macro's outline ("Failed to extract PR boundary from GDSII view of macro").
# Usage: klayout -b -r add_prboundary.py -rd gds=<in.gds> -rd out=<out.gds> -rd w=<um> -rd h=<um>
import pya

layout = pya.Layout()
layout.read(gds)  # noqa: F821 (set by -rd)
top = layout.top_cell()
dbu = layout.dbu
li = layout.layer(189, 4)
top.shapes(li).clear()
top.shapes(li).insert(pya.Box(0, 0, int(round(float(w) / dbu)), int(round(float(h) / dbu))))  # noqa: F821
layout.write(out)  # noqa: F821
print(f"prBoundary 189/4: 0 0 {w} {h} on {top.name}")  # noqa: F821

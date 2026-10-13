# Best133 congestion and native reflow regression audit

The native-feedback reflow is rejected. [Paired run38453870785](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38453870785) preserves native routing failures: best control133 versus candidate6000 overflow. The strongest new clue is thousands of **zero-capacity edges within the macro footprint**, rather than a modest increase in shell congestion. This does not prove a router bug or justify removing obstructions.

Result SHA256: `c840a2cb627f96eb15cb1a45252728c8a7ed187f5d8fa1cb47f1299f996a3329`.

## Authenticated observations

The report parser verifies source digest and native capacity/usage/overflow arithmetic. The existing membership audit resolves **every marker net** in each corresponding input census; no missing-net join was found. Group memberships overlap and cannot identify independent contributions.

| Measurement | Best133 control | Native feedback candidate |
|---|---:|---:|
| Native final overflow |133|6000|
| Planar markers |91|5367|
| Zero-capacity markers |10|5267|
| Marker boxes overlapping macro footprint |16|5299|
| Markers wholly west of macro |68|1|
| Markers wholly south |6|33|
| Markers wholly north |1|34|
| Metal1 routing resource |16596|13283|
| Metal1 final overflow |13|3442|
| Metal2 final overflow |53|1795|
| Metal3 final overflow |31|745|
| Metal4 final overflow |36|18|

Macro footprint is x121.44–1241.76,y15.12–684.18µm. Region classification uses entire marker boxes; boxes crossing a macro boundary enter the overlapping category. Native report layers are unset (`-`), so planar markers are not assigned to individual physical layers. Their summed overflow happens to match the final table here; the parser does not require this generally.

Report hashes:

- Control: `8e2f5c5003e495d3d347be7d593bb4bbc7801723db2902c3cb530e70a157a1df`.
- Candidate: `7958be1270cc337b5134049c9ff3b4aebbdc6df988b99c296d508a8f282c2cc2`.

Actual instance **origins**, excluding macro, classify control west3234/south290/north74/east7; candidate west2921/south312/north439/east7. No standard-cell origin is inside the macro. These are origin counts, deliberately distinct from earlier full-cell-rectangle corridor counts. Exact macro position/status is retained by the producer.

Candidate repeated sources include clock leaf15 (184 markers), net96 (176), ui_in[6] (173), uo_out[4] (171), and uo_out[6] (169). Thus the regression affects top I/O and clock/configuration paths; it is not exclusively CRC or antenna repair. Observed candidate zero-capacity marker coordinates include x655.2–662.4/y187.2–194.4 for uo_out[5], deep in the macro footprint.

## Remaining control hotspots

Of68 west-channel markers,46 start in y450–500µm and17 in y500–550µm. This retains the historically observed CRC/SPI west-channel concentration. Overlapping control membership counts include CRC67, SPI45, clock39, fabric boundary35 and configuration35. These counts do not prove that removing any one function removes congestion.

Control zero-capacity edges are a different small problem: seven of the ten name cell_val[30] around x115.2–158.4/y14.4–36; three name cell_pad[27] and sometimes cell_pad[31]/cell_val[27] around x273.6–302.4/y14.4–21.6. Actual pin rectangles and obstruction boundaries are needed before proposing a fix for these paths.

## Interpretation and next bounded diagnostic

The artifact's macro LEF declares full-footprint Metal1–Metal4 OBS rectangles. These are necessary abstract-view restrictions unless a separately validated abstract proves a legal route-through region. Moving more related shell cells to the opposite macro edge plausibly creates long routes around this blocked region. Zero-capacity paths inside the macro establish an infeasible allocation in the failed router result; they do **not** establish why the router selected it, nor prove the macro pin abstraction is malformed.

Global layer capacity averages are also misleading: the best control has only33.16% aggregate reported usage yet fails localized edges. Native-feedback placement did not prevent the candidate from attempting blocked crossings. Another broad placement/density sweep has no evidence-based justification at this point.

The next experiment is read-only: export transformed signal pin rectangles for every actual instance including u_fabric, top boundary pin shapes, macro-local OBS with explicit origin/orientation, block OBS, and DEF tracks/rows/special wiring from the exact best133 ODB. `test_internal/cloud_boundary_audit.py` and `.github/workflows/boundary_audit.yaml` implement this using the pinned cloud OpenROAD image. They authenticate all five recorded producer views before and after, require3606 instances/nonempty macro/boundary pins, retain hashes and never run placement/repair/routing. Python imports are standard-library-only. Actual producer authentication and Python syntax/import checks passed locally; native exporter execution remains a cloud validation obligation.

The collector uses `dbITerm.getGeometries`, already exercised by our existing route geometry exporter, and the [OpenDB APIs for master/block obstructions and pins](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/odb/include/odb/db.h). Master OBS coordinates remain explicitly local, avoiding a hidden transform assumption; the collector requires the actual R0 macro orientation. DEF preserves track declarations without inventing a track-grid API.

After export: join those ten zero-capacity markers to their exact endpoint shapes and nearest OBS/track boundaries, then quantify the west-channel y450–550 cut with true pin endpoints. Choose one local intervention only if that evidence isolates one. Retain the measured133 control; no source hardware, margins, capacities, layer policy or phase gate changes are made by this audit.

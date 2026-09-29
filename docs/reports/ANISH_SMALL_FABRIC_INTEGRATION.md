# Small mapped fabric: integration dependencies — 2026-09-28

The next milestone is a compiled circuit executing on a small, dynamically
loaded mapped fabric. It is not another isolated loader cost comparison.
This source audit defines what must change before that test is credible.

## Verified starting point

`build/small-fabric-integration-audit-20260928.json` records checks against
the retained generated fabric and both mapped tile variants:

- Reference grid: 14 logic rows, 10 columns, 84 LUT tiles. It also contains
  register-file, DSP and RAM-related tiles; shrinking only LUT count is not
  a complete small-fabric design.
- Both compiled reference images have the expected 12,024-byte length:
  20 header bytes + 10 columns × 20 frames × (address + 14 row words) ×
  4 bytes + 4 footer bytes.
- Every stock/held tile port's direction and width survives mapping.
  ReloadHold is the held variant's only additional port. This supports
  substitution at the tile boundary, not whole-fabric functional equivalence.

## Required adaptations

| Component | Current dependency | Required small-fabric change |
|---|---|---|
| Fabric generator | Large reference grid and tile set | New isolated definition with required I/O and edge wiring; no RAM/DSP unless needed by the demonstration |
| Hold patch | Hashes of this generated reference; exactly 84 LUT tile instances | Separate checked generation/patch path with counts derived from the new grid; preserve the old strict checks |
| Image validator | FRB1 ID, 12,024 bytes, footer word 3,005, 14 rows, 20 frames | New architecture identity and geometry-derived limits after inspecting the generated image; reject cross-architecture images |
| Image decoder/tests | Same geometry plus fixed mutation offsets | Independent small-format decoder and fresh bad-image vectors; retain the existing reference tests unchanged |
| Loader | Pinned parameterized FSM, but fixtures assume 14 rows | Instantiate actual generated dimensions and verify every accepted word/frame and staging bit |
| Testbench | 28 reference I/O bits, counter/LFSR ABI, fixed image size | Public-port oracle for a freshly compiled small circuit, coordinated reset/hold release and wrong-function control |
| Physical top | Placeholder adder; experimental RTL excluded | Integrate only after the small mapped functional gate; keep source lists, pin contract and testbench synchronized |

Do not reuse the large reference bitstream on a cropped fabric or merely
relax its length check. Do not tie configuration to constants for area or
chip-build validation. The existing four-clock word pacing remains the
conservative starting point until tested with the selected loader geometry.

## Implementation order and acceptance

1. Generate the smallest practical connected fabric in an isolated build,
   retaining upstream edge conventions. Try a small counter first; freeze
   dimensions only when synthesis and place-and-route compile it successfully.
2. Record the generated grid, tool versions, actual frame layout and image
   hash. Derive validator bounds and counter widths from that format, with
   an explicit distinct identity. Keep the software decoder independent.
3. Map logic and configuration storage without pruning state; load through
   the real word interface. Require counter progression, reset, enable,
   first visible output, reload, interrupted-load recovery, checksum and
   wrong-architecture rejection on the mapped implementation.
4. Only then prepare the Tiny Tapeout integration and physical run. Report
   routing/DRC/LVS and timing at each corner separately. Programmable
   feedback and configuration timing need explicit treatment; a zero
   black-box connectivity count does not waive them.

This plan does not freeze the production host protocol, promise protocol
capacity, or close phase 0. The current bitstream and patch tools are
intentionally reference-specific; this is planned adaptation, not a defect
in their stated scope. No new RTL/GL or GDS build was run for this audit.

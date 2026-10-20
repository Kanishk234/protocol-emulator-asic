# Native physical-to-coarse terminal qualification

[Run 39367564921](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39367564921),
at `8782e284e94706486f20f25248c7067eecdf0d70`, attempt 1, succeeds as a
bounded diagnostic. It uses successful build 39333325323. Original result
SHA256: `8ac9ecbb64903a9296cd7cb6fd36633417933d9723e041537ea79091a1f73674`.

The coordinator and independent reviewer reparse all six raw/terminal pairs.
The portable audit verifies Git-object hashes of all four patches, separate API
identity, exact 121/132/139 reporting controls, every raw usage ledger, all raw
capacity/reduction/real-capacity fields, native completion witnesses, inventories
and stored-result equality. Unchanged initial/default-final raw and terminal
snapshots are byte-identical. Terminal SHA256 is
`90be2ecef64627ed67b1c4df920f86f673cac1bcdae4fef4db9587a3e79a18d3`;
raw SHA256 remains `1859f6fdaffad9977ab4025867332a5835e68f50b86405719447b1b3c1aa07e6`.

Each state records 3,693 database nets, 3,691 GlobalRouter nets, 3,659 native
nets, 10,888 observed physical pins and 10,856 memberships. The global terminal
gate correctly remains **FAIL**, with the same diagnostic classes in all six:

- 285 local native nets with empty trees (278 one-pin and 7 two-pin).
- 32 local one-pin GlobalRouter nets without a native net.
- VPWR/VGND supply nets outside the GlobalRouter membership map.

Those observations are preserved, not promoted to whole-inventory support.
The original southern targets, slots 98/122, have no unsupported entry in any
snapshot and have exact five physical-to-native memberships. Their coarse pin
vectors, driver indices and node mappings are supported; physical via legality
and frozen-exterior extraction are separate obligations.

The explicit selected-admission helper in a3eb447 preserves the whole gate
while admitting a named cohort only if every selected membership/access passes
and the raw usage ledger reconciles. It never elevates native/physical/timing
authentication. The later five-net southern cohort also passes that scoped gate.

Local full autonomy suite before extraction: 545 executed passes; after selected
admission/extraction: 567 executed passes. Strict XML confirms zero skips/errors/
failures in both. Source review caught and fixed the leaf-clock classification
error before native testing (BUG103). Independent actual review is in
[native_terminal_result_review_20261019.md](native_terminal_result_review_20261019.md).
No routing improvement, configured-silicon timing or physical acceptance follows.

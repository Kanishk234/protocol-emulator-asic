# Claims

Every public claim about the chip, with its evidence. If there is no evidence, it is not a claim.

| # | Claim | Evidence (run ID / report / proof log) | Status |
|---|---|---|---|
| C1 | A 16-LUT FABulous fabric (stock `LUT4x8_ha` tiles, CMOS5L patch D-010/D-017) hardened as a macro inside a Tiny Tapeout 6x4 IHP CMOS5L project passes TT's template `gds` flow, precheck (9/9) and `gl_test`, with DRC, LVS and antenna at 0 | CI run 36327510268 (dea2150); `docs/reports/fabric_tiny.md` | holds (phase 1 spike; not the final chip) |
| C2 | On CMOS5L, a FABulous LUT4 costs ~5,090 µm² including its configuration latches, switch matrix and routing (tile `LUT4x8_ha`, 40,719 µm² per 8 LUT4, routed within Metal2–Metal4, KLayout DRC 0) | local tile runs 2026-09-25/26, `docs/reports/tile_cmos5l.md` (no CI run: tiles are hardened locally) | measurement, local only |
| C3 | The four design-set protocol user designs pass RTL tests against reference models and sigrok decoders in several configurations | CI `unit` 36211778569 and later; `protocols/*/README.md` | holds (RTL simulation only, not on the fabric yet) |

Not claimed: "first FPGA on Tiny Tapeout IHP" or similar (Tiny FABulous exists on SKY130 and FABulous has IHP tapeouts; `docs/notes/prior_art.md`); any user-design rate or fabric timing (not measured yet).

## Never claim
- USB or Ethernet support, real-hardware testing, or "formally verified" without the property and bound.
- Any area, timing, clock or protocol-rate number without the run ID.
- Superiority over a CPU/PIO design or a generic fabric without an equal-area measurement.
- Generality beyond the held-out results.
- "First" or "novel" without a prior-art check.

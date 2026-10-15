# Current-source design-set profiling refresh

Hosted38780941523 succeeds on8e4c117537401528814ff25fadd64de697654db5 using
Yosys0.66+179/e74db6dea and the pinned2026-06-29 suite. It runs the four
already-profiled design-set sources across all six LUT/carry variants, retains
all24 native JSON outputs, and records parameters, hand-reviewed role tables,
Python/tool versions and listed-input/output fingerprints. No held-out input,
physical area, timing or native-chip acceptance is measured.

Independent post-download checks match every listed input to `git show` at
that exact revision, verify output fingerprints, and directly count native
LUT/FF cells in all24 netlists against the emitted rows. Current no-carry LUT4
totals are UART144, SPI85, I2C controller141 and I2C target185: total555.
These are current-source synthesis counts; they do not retroactively replace
the original phase1 profile648 or measure placed fabric capacity.
Result SHA256:
`e9d0b5c42548c0f9d4cfffd86f5c5c971eea94aea73afeccd5c77460f8bc9497`.

Review also catches BUG93: the I2C target's current plain-logic state names
`g_logic.n`/`g_logic.sr` no longer match the historical `nbit`/`shift` role
regexes. The first refresh's target function breakdown is therefore not
accepted as a reviewed profile, although its185-LUT census is valid. Extend
only those role matches and rerun; retained netlist reanalysis restores four
counter and eight shift FFs without changing the cell total. The collector
now rejects a conserving matrix that loses the expected timing/shift state.
Actual corrected hosted refresh is pending; no corrected shares are claimed
from local synthesis. Reanalysis uses retained JSON only, no local EDA.

**Actual corrected refresh:**38820879331SUCCESS at
f8ed2a0a74030f0d1e4a6cb2445ba9dd730ec61b. Downloaded listed-source hashes
match exact Git bytes, both output fingerprints match and all24conservation/
expected-state checks pass. LUT4total remains555; corrected categories are
counter125, shift105, storage100, control107, shared88, pin27, sync3.
All four workloads retain identified counter and shift state. Result SHA256:
`be18a833a62b9461446d68cbcc79ad51360776ae48fe4a7e94a639c37f76e224`.
This closes the fresh profile's attribution defect; original phase1 tables
remain historical data, and no chip area or validated rate follows.

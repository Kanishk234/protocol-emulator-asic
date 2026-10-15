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

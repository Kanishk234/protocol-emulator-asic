# Compiler failure classification

Date: 2026-10-14. Frozen-baseline software diagnostics only.

The compiler already rejects pin-map duplicates, conflicting IO roles, missing
strict ports and measured resource over-capacity. These checks remain intact.
Its place/route failure advice previously used a shared generic message whenever
resource usage stayed within capacity; `failure.json` did not distinguish a
reported routing failure from a legal-placement failure.

The diagnostic now adds `diagnosis` with a conservative `category`, original
`fatal_messages`, measured `over_capacity` entries and actionable `advice`:

- `resource_capacity`: actual used/available counts exceed capacity.
- `placement`: fatal output says placement failed for a cell or no BELs remain,
  without measured over-capacity. Compatible sites and reset/enable constraints
  may limit fit even when aggregate resource counts fit.
- `routing`: fatal output explicitly reports inability to route; advice directs
  attention to reported nets, pin positions, fanout and seed comparisons.
- `unknown`: no recognized evidence; retain the existing generic guidance.

Only fatal lines classify placement/routing. Informational text about a failed
intermediate attempt cannot classify the final failure. Raw errors, tool
versions, seed and utilisation remain in the report. No successful compilation,
hardware, mapping, pin assignment or held-out tuning behavior changes. Seed
comparison is advice, not evidence that a design will route.

Validation in the project `.venv`:

```
python -m pytest -q tools/compile/tests/test_diagnostics.py tools/compile/tests/test_bitgen.py tools/compile/tests/test_audit.py
58 passed in 16.95s
```

Tests cover over-capacity versus compatible-site failure, missing utilisation,
explicit routing failure with net preservation, unknown-message fallback,
nonfatal-message rejection, seed preservation and stale-image handling. The
retained actual design-set log
`build/compiler_fit_diagnostic_20261005/pnr_stdout.log` also classified as
`resource_capacity` with `FABULOUS_LC: 95/88`. This is local parser evidence,
not a new compilation or CI run. No physical tool run was needed. Routing-message
fixtures are synthetic; unrecognized future vendor wording remains unknown.

## Repeated parameter-option fix (BUG85)

Actual cloud run 38676021166 exposed a CLI issue: repeated `--set` options
silently discarded the earlier parameter group, so an intended larger counter
retained its default width. The parser now extends parameter groups rather than
replacing them. A single group remains supported; repeated names retain the
existing last-value-wins behavior. Three mocked CLI regressions verify the
single-group form, separate groups and repeated-name precedence without EDA.

Local focused validation after this fix: `python -m pytest -q
tools/compile/tests/test_diagnostics.py` — **15 passed in 0.27s**. This tests the
parser-to-compiler parameter contract; root separately verifies actual compiled
parameters and loaded waveforms in cloud. No hardware or parameter defaults
changed.

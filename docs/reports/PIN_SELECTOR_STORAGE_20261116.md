# Pin-selector storage follow-up

The cache trial is functionally green, but its physical screen stops on one
antenna violation. It is not eligible for detailed routing. The follow-up now passes cloud regression 43946078700; its physical
screen is being prepared. It has no routed or extracted timing result yet.

- Functional run: [42724791204](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42724791204),
  exact a82fa83, attempt 1. Complete 395,219-byte archive SHA256 matches API;
  actual XML verifies 335 model/compiler, 4 top and 22 protocol cases, no
  failures/errors/skips. Source and single-file delta checked; compact receipt
  is `cache_regression_42724791204.json`.
- Physical run: [42725043665](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42725043665).
  Original estimated fast hold is 0.0959032 ns, setup WS 0 all corners,
  electrical counts 0 and global overflow 0. Final antenna is 1 net/1 pin.
  U0 word-1 configuration clock violates Metal3 cumulative ratio 225.55/200
  at `_48786_/GATE`. Earlier native repair's checker reports zero.
- Follow-up: only word-1 stored configuration bits move to write-enabled
  root-clock flops, on top of the existing cache trial. All values and reset
  visibility are retained. See D-174 for general need and cost.
- Local module checks pass for full and lean variants: 665,780 phase
  comparisons each, all 459/557 equivalence points using induction cap 6,
  registered host writes, no blacklists, wrong-reset mutation detected.
  `pin_select_module_20261116.json` records the compact result. Raw logs remain
  in `/tmp/tripwire-select-ff-20261116`.

The new `tripwire-pin-select-trial.yaml` first reproduces the cache proof,
then proves/applies this follow-up, runs model/compiler and actual-top/protocol
suites, and checks that all receipt inputs remain unchanged except the bound
configuration file. Published in 9ee952c, selector regression
[43946078700](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/43946078700)
is queued on that exact source; physical
screening must wait for its actual passing artifact. No production RTL/config
or protected template job changes. No phase checklist boxes ticked.

Large physical/clock artifacts were read by selected ZIP ranges with per-entry
CRC verification, not locally whole-archive hashed. Their API digests and this
limitation are retained in `closure_followup_20261116.json`. The small functional
archive was fully downloaded and digest verified.

## Publication and reproduction

The user subsequently renewed session approval for grouped commits and pushes.
The commands below document the publication groups; the worklog records actual
publication and cloud run receipts. Run on `tripwire/closure-8x4` after reviewing
the diff. Existing unrelated untracked artifacts are deliberately excluded.

```sh
git add spikes/phase2_stock_flow/pin_select_word_ff
git commit -m 'rtl: prepare pin selector storage trial'

git add scripts/ci/verify_bitsync_cache_ff.py scripts/ci/verify_pin_select_ff.py
git commit -m 'tools: verify selector storage equivalence'

git add .github/workflows/tripwire-pin-select-trial.yaml .github/workflows/tripwire-bitsync-cache-trial.yaml
git commit -m 'ci: check pin selector storage trial'

git add docs/BUGS.md docs/CLAIMS.md docs/DECISIONS.md docs/WORKLOG.md docs/design/PHYSICAL_DESIGN_AND_CI.md docs/summaries/PHASE2.md docs/reports/PIN_SELECTOR_STORAGE_20261116.md docs/reports/cache_regression_42724791204.json docs/reports/closure_followup_20261116.json docs/reports/pin_select_module_20261116.json
git commit -m 'docs: record cache results and selector follow-up'

git log origin/main..main -- src info.yaml macro
git log origin/tripwire/closure-8x4..HEAD -- src info.yaml macro
git push origin HEAD:tripwire/closure-8x4
```

Before pushing during any active hardening, check both logs above: hardware
changes can cancel a running hardening. This prepared change adds an isolated
patch experiment and workflow; it does not change production `src/`,
`info.yaml`, or `macro/`. Publishing the new workflow starts functional
verification; it does not automatically launch another physical screen.

The separate fixed-route diagnostic
[42724400182](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42724400182)
reproduces the original extracted slow setup (-1.982448040 ns at 20 ns);
21 ns still fails (-0.982447929 ns). Tested 22, 24 and 25 ns cases report
setup WS 0 at all corners, with unchanged hold and zero electrical violations.
All corner values match the retained per-period raw metrics. This is a
fixed-RC diagnostic that also changes stock period-derived constraints, not
a clock-contract change, demonstrated positive setup reserve, or signoff.
The repair effort keeps the 20 ns target.


## Same-clock physical screening

Selector regression 43946078700 is now independently checked: all 335/4/22
actual test cases pass, the full archive digest matches API, and 34 available
source files match the one-file-delta receipt. Compact evidence is in
`selector_regression_43946078700.json`.

`tripwire-pin-select-screen.yaml` admits that exact successful run before
preparing the cache baseline plus the selector-only patch. Original stock
measurement and acceptance scripts stay unchanged; the structural guard checks
both cache and selector workflows. No change to 20 ns, live reconfiguration,
production config or protected template jobs. A passing pre-routing screen
will still need detailed routing, extracted timing, final replay and official
GDS/precheck before release qualification.

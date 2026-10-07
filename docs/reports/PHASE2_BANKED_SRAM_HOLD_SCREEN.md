# Banked selector SRAM hold repair-only screen

The corrected paired screen37669663762 reports one fast hold violation, lane1 acc_addr[8] to SRAM A_ADDR[8], -0.0223693 ns. All three setup violation counts are zero; slow/typ hold counts are zero. Baseline event-late has +0.0313302 ns fast hold. This banked candidate is not eligible for direct routing or official promotion.

## Prepared experiment

`.github/workflows/gds-banked-sram-hold-screen.yaml` accepts only a manual trigger and binds source run37669663762 and bs-event-pin-banked. Frozen candidate3393eea source fingerprints are constructed from the trusted named patch before download, then checked against the successful main source workflow and every saved source/macro hash. IO fingerprint is mandatory. No main hardware/config/template job changes.

`scripts/ci/banked_sram_hold_screen.py` requires exactly the audited source run, nonnegative all-corner setup with zero setup violations, one fast hold violation between -25ps and zero and no slow/typ hold failures. Actual checkpoint/config/constraints and source identity are rechecked before invoking pinned LibreLane3.1.0.dev3.

The independent image layers a narrow wrapper over the existing Metal2 reservation wrapper. Only the post-GRT resizer script is patched, immediately after its unique checkpoint read. The Tcl helper accepts only net9161, BUF2 wire9161/X and SRAM A_ADDR[8]; changed connectivity/master/power or duplicate insertion is rejected. One BUF1 is placed provisionally next to the driver, followed by normal detailed placement and one all-corner repair targeting125ps hold, zero setup margin. Placement/repair/route changes can affect other endpoints; the buffer is not assumed to improve hold.

The workflow runs fresh per-corner timing, checks execution evidence for both physical insertion and region reservation, runs antenna check/repair/recheck and fresh timing again. Readiness requires nonnegative setup/hold and zero violations at all corners, at least50ps fast hold, and zero antenna violations. Detailed routing is absent. Failed readiness is reported as a workflow failure while uploading evidence. Passing these estimated gates would justify reviewing a routed follow-up, not establish extracted closure.

## Verification and limits

217 local helper tests pass, including exact source bounds, final headroom/antenna policy, malformed checkpoint-read refusal, injection ordering and five Tcl connectivity guards; no skips in the new Tcl checks. Bash syntax and git diff checks pass. Earlier RTL verification covers the source candidate:60pin/5chip/2048clock lockstep. Local physical execution remains untested because cached OpenROAD lacks libQt5Charts.so.5; pinned CI must establish real insertion/legalization/route/timing behavior. No workflow dispatched yet.

Publication groups: tools/tests/image wrappers; new manual workflow; reports/BUGS/WORKLOG separately. Keep FIPE review and unrelated old SRAM addr0 helper local. Prepared gds-placement-route changes are not required for this repair-only dispatch and should remain separate until routed follow-up is justified.

Once the required tool/workflow groups are published, launch:

```sh
gh workflow run gds-banked-sram-hold-screen.yaml --repo Kanishk234/protocol-emulator-asic --ref main
```

Original125ps event-late remains the strongest measured extracted setup baseline (-0.179789ns setup, +0.037290ns fast hold). This experiment must improve measured feasibility rather than displace that baseline on an unverified claim.

First run37689090398 aborts before insertion because resizer step config lacks placement-only PL_TARGET_DENSITY_PCT (BUG75). Corrected guard checks density/timing mode in base and unique actual global-placement config; repair config still checks clock/GRT/mirroring/SDC.224 helper tests and replay of actual downloaded source configs pass (runner absolute SDC path rebased only for local audit). This failure supplies no physical timing evidence.

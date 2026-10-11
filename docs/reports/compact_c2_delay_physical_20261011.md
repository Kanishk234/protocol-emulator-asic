# Eight-delay C2: actual physical evidence and remaining gates

## Actual loaded-function follow-up

[38163199372](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38163199372) SUCCESS. Fresh original controls regenerate from the already-approved checkpoint and retain exact required hashes, avoiding expired37659171115 artifacts. Independent XML/log checks verify all four control/candidate normal/USER_RESET cases, all9164 actual configuration latches known and image-matched,28 UART TX/28 RX stress bytes per case and STOP parking. Candidate final netlist remains exactlya986a0864ab51f09f6157422ba7dff935585b6456e6accc7b64ac8228725e882. Actual result SHA97bcb3cec7bbb006bd99c94250618980fa1f5493e6338d5502411dc44cb6abb8; candidate matched mapped graph SHA313a7c727a0105813daef7b12efa1b52b921663905089cc902a2450d882fb5a4. Only C2 is substituted; other tile types are regenerated controls, no SDF/full-chip/timing claim.

Fresh conditional extracted timing from this actual candidate graph/image and its own routed views now completes38164099529: all six examined cases clear setup/hold, worst hold+0.042992ns. BothX2Y1/X2Y3 configuration bindings and eight clock endpoints per position are audited. The new nominal SPEF SHA7343e224529b757b74824836b5491af24f656a1d0bee7a92b1e396ce5b42fcfb replaces the old tile SPEF; three actual libraries and original20ns/.25ns uncertainty/.15ns transition/5% derating remain. No I/O constraints, loop cuts or user-state cases; configuration Q stationary is a diagnostic premise. See [extracted report](compact_c2_delay_extracted_20261011.md) for path counts, annotation and coverage limitations; no full-chip timing acceptance.

Cloud run [38114298036](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38114298036), commit42afad7, ran from05:17:17 to05:27:22UTC (10m05s including provisioning). This is D-077's copied-input macro experiment, not a full-chip promotion.

The final retained checkpoint is stage62 report-manufacturability. Actual metrics show routing DRC0, antenna nets0/pins0, critical disconnected pins0, Magic DRC0, KLayout DRC0 and LVS errors0. Detailed-routing iterations report229→63→24→0 errors, with subsequent iterations also0. Native original/final signal and power inventories are structurally identical;306 signal ports retain their original geometry. All eight generic delay instances remain in the final mapped netlist.

The workflow conclusion is **failure**. Original virtual-clock setup checks still fail: actual setup worst slacks are fast−3.708546ns, slow−26.089773ns and typical−12.025222ns. These clocks do not establish programmed internal timing. An additional reporting defect (BUG69) prevents the physical-summary JSON from being written because native LibreLane metrics include Decimal values. Neither error is erased by the separate physical-gate evidence.

Authenticated retained evidence:

| File | SHA256 |
|---|---|
| result.json | 61e0a7ebc13fca49b0b1eb0c91ad7288031628edd3c43a428104023b0de42512 |
| input_change.json | c078464eb1f1b1cc6eef8dc7e063b03b53a74fded56df7b0bf0ac6b6a20163f4 |
| final netlist | a986a0864ab51f09f6157422ba7dff935585b6456e6accc7b64ac8228725e882 |
| final metrics | 0e89d954fb8f51d8ca95df7b34c864e7b9cf5fb0ebff141f74a3261918a81cfa |
| final pin inventory | e4fe52ec667bf54d95bc4db23d874505ca8a1e789eca4b6a65c9891590bb3efc |
| reference pin inventory | c05b64c5e31b274c5c6ac926c0646b5e980c515c4fb5af1b015edb2c76658ea4 |

The inventory hashes differ because their JSON serialization orders differ; parsed contents are exactly equal. All gates/instances/interfaces are checked by cloud_c2_delay_loaded.py before simulation.

Next: load this exact newly routed netlist through the unchanged real SPI configuration harness and compare normal/USER_RESET cases against the original passing control. Other tile types remain regenerated control views, so this is C2-specific evidence. Then evaluate the candidate with its own extracted SPEF, stationary programmed configuration and actual internal clock. Preliminary intrinsic positive hold slack does not guarantee extracted hold closure. Full-chip electrical fanout, intertile/shell clock paths, loading-mode timing and I/O remain open.

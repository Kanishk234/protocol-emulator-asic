# Eight-delay C2: actual physical evidence and remaining gates

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

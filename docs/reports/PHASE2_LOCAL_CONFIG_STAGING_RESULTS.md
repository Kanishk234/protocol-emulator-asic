# Configuration locality experiments (2026-11-12)

These are local 8×4, two-lane/four-unit studies against native-drive source43178099947. Main hardware/config and the official GDS jobs are unchanged. The current physical measurement is TX-cursor screen43338175616; none of the source experiments below has a native physical result.

| Variant | Mapped area (µm²) | Slow worst flop slack (ns) | Flop endpoints | Decision |
|---|---:|---:|---:|---|
| Reference | 411236.0280 | 5.614 | 2414 | Matched local control |
| Four data banks, retaining carrier staging | 422001.5436 | 4.471 | 2545 | Reject before physical screening |
| Cached owner mask / parallel pad qualification | 415082.2158 | 5.451 | 2470 | Reject: BITSYNC timer also regresses |
| Dedicated selector/event-word data bank | 414652.8078 | 6.082 | 2458 | Local candidate;22/22 RTL protocols pass |

Mapping uses the same NAND2_1/NOR3_1 exclusions, ideal20ns clock and no routed parasitics. It is not native signoff timing. The reference source is the same for all four rows; generated physical config files do not participate in the local synthesis recipe.

## Rejected broad variants

The naive four-bank rewrite initially changed the cached carrier-enable value under high-phase bus motion. The ordinary phase simulation missed it; full-output phase proof and a targeted sparse-data test caught it. The revised prototype preserves the original predicate staging; FULL=0/1 proofs pass429/561 points, the targeted test passes and each exhaustive word3 test passes133152cycles/665760comparisons. It still increases area about2.62% and regresses setup, so no physical run is justified.

The owner cache is proved for NU=4/6 using a full miter with the additional checked invariant that the cached mask equals the binary-owner decoder. Temporal induction succeeds at step2 after a synchronous reset; future owner writes, pin mappings and data are unconstrained. This is not a one-hot assumption. The randomized six-unit pad-owner scoreboard passes. The simpler correspondence proof was insufficient and is not counted as passing. Local slow TX/fabric/BITSYNC timer group slack is5.634713/6.610379/5.698084ns versus5.901533/6.677540/6.544236ns reference. Reject it before protocol or physical runs.

## Narrow staging candidate

`spikes/phase2_stock_flow/input_word_bank/input_word_bank.patch` adds a dedicated root-clock staged-data bank for the configuration word containing PIN_N and event controls. The existing word latches, gates, even/odd stages and carrier predicate remain. This is a general configuration-locality change; no protocol-specific block, state encoding or extra architectural cycle is introduced.

It targets the reference's single antenna offender: a long staged-data branch into unit1 word3 bit3. Smaller fanout and a dedicated source register may improve locality, but no routed or antenna improvement is claimed.44 extra flops survive mapping; latch count remains2071. FULL=0/1 phase proofs pass461/560 points, both exhaustive tests pass133152cycles/665760comparisons, and the wrong-word staging mutant fails proof.

Slow TX/fabric/BITSYNC timer group slack is6.483136/6.841258/6.081669ns. SRAM-origin slack is6.173ns versus6.557ns reference. Thus the global minimum and fabric improve, while BITSYNC and SRAM regress. These tradeoffs must remain visible when considering any native test. The22-case protocol replay passes22/22 with no failed/skipped cases (415.76s); no separate screen is prepared or launched. On the existing TX-cursor source, adding the bank changes mapped area415168.4376→417164.0508µm², slow minimum5.848→5.854ns (essentially unchanged), and SRAM slack5.848→6.285ns. The combined source passes22/22 local protocol replay cases, zero failed/skipped (362.01s), with source/XML hashes recorded in candidate.json; it has no physical run. Three applicator tests pass; source application preserves the exact TX and physical-config hashes.

## Independent lint cleanup

`spikes/phase2_stock_flow/c_pad_width/c_pad_width.patch` sizes the C-pad loop-index comparison to five bits. The module proof passes53 points; a deliberately four-bit comparison fails. Strict unfiltered whole-chip Verilator lint passes both the prepared native-drive reference and current TX-cursor source with this sole cleanup. It is ready for future integration; it is not applied to main or the active screen, does not alter historical patches/receipts, and makes no physical timing claim.

Raw outputs remain in `/tmp/tripwire-cfg-four-banks`, `/tmp/tripwire-owner-cache`, `/tmp/tripwire-cfg-input-bank`, `/tmp/tripwire-tx-input-bank` and `/tmp/tripwire-cpad-width-clean`.


## Timing-library consistency

The typical and slow standard-cell Liberty files used by the local recipe were fetched from the native screen's pinned IHP PDK revision89d42ee6d2fd9b50b86a1aada6fee6673c3e6008 and compared byte-for-byte with the cached2bbec755dc67ca3db0261c3d6163e15735d66710 files. Both match; SHA256 receipts are in the narrow candidate metadata. This checks those timing files only. The local mapping engine, ideal clock, parasitics and constraints still differ from native physical signoff.

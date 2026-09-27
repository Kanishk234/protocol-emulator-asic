# Loading-order and isolation experiments — 2026-09-26

**The minimal LUT/carry hold candidate passes A/B/A, B/A/B, wraparound,
and two interrupted-load recovery cases.
Stock-fabric reload remains broken; this is not yet a production repair.**

Follow-up: [guarded reload and CMOS5L measurements](ANISH_GUARDED_RELOAD.md)
adds actual output parking, reset-before-pad-release, invalid-commit checks
and isolated mapped-netlist evidence. That wrapper still trusts its image
validity input and does not establish full-chip timing or isolation coverage.

Same stock reference build and images as [the original report](ANISH_REFERENCE.md):
counter SHA-256 `3788d987158d0e81683cbf1378c0749d57c4f0c265d797483f50d6f004fc5874`,
LFSR SHA-256 `774c910855a69986347d34072b557dac900bb2dd5556e9f365776ea5f3cec8fd`.
No synthesis/P&R of user designs was repeated. Original fabric source remains
unchanged; only the isolated candidate source copy differs.

## Loading experiments

| Variant | Observed result | Retained evidence under `build/` |
|---|---|---|
| Reverse all 200 addressed frame records | Both directions time out, exit 124 | `warp-order.zZxwIQcV` |
| Clear all frames within each column, columns descending, then canonical image | Both directions time out, exit 124 | `warp-order.3Y62hoNv` |
| Hold LUT/carry outputs low throughout canonical upload | Both directions complete, exit 0, 2,479 checked cycles each | `warp-order.Q6ZUMUHn` |

Reverse-order manifests retain every address and payload exactly once.
The first direction stalls at upload byte 10276 (column 1/frame 9); the
reverse direction stalls at byte 9796 (column 1/frame 17). Reordering merely
changes the failing intermediate state for this pair.

The clear stream is 624 bytes: sync header, ten column writes with frame
mask `0xFFFFF` and all-zero row data, then desync. It uses the actual public
word loader, not a force/deposit. In A/B/A, the counter and subsequent clear
complete, then LFSR loading stalls at byte 1816 (column 1/frame 9). In B/A/B,
the very first LFSR upload after clearing stalls there. Thus startup success
from unknown configuration is insufficient evidence for startup/reload from
a known cleared state. This does not prove that every possible clear order
fails; only this tested sequence failed.

The first two exploratory runners were edited while their shells remained
active. Their simulations produced the recorded timeouts, but subsequent
shell parsing also failed (and one status line was duplicated). Do not cite
their overall shell status as a clean regression result. The new runner
executes an immutable copy under `build/` and retains it. The hold run ended
normally and has both explicit behavioral PASS markers.

## Isolation candidate

ANISH-D2 introduces `ReloadHold` as an ordinary input on a copied reference
top, fabric, LUT tile and LUT primitive. When asserted, each LUT's ordinary
output and carry output is clamped to zero. The public loader remains live.
No internal state is forced; configuration is still written by actual frames.
The compiled user images and configuration-bit assignments do not change.

The patch transformer verifies four original source hashes before applying
changes and preserves upstream license headers in the copies. Each run
retains a unified patch and before/after hashes. It is specific to this
reference build, not yet integrated into FABulous generation or chip RTL.

The primitive test passes 256 held/released vectors, checking the LUT truth
table, registered reset value and carry arithmetic, plus isolation while
configuration and inputs are unknown. The full-fabric quick runs check
reset priority, disabled hold, pseudorandom enables, output data and output
enables in both directions. Full wraparound and interrupted-load validation
are recorded below.

## Extended validation

Retained run `build/warp-order.eg3GdZkQ/` completed normally using a captured
runner and the same source patch. All expected markers and exit codes agree:

| Case | Checked cycles | Exit | Result |
|---|---:|---:|---|
| Full A/B/A, including 16-bit counter wraparound | 67,987 | 0 | PASS |
| Interrupt B after 33 complete frames, reset loader and restore A | 1,322 | 0 | PASS |
| Interrupt B after 199 complete frames, reset loader and restore A | 1,322 | 0 | PASS |
| Load B while expecting counter A | first reset check | 1 | Expected functional failure: ACE1 versus 0000 |

The interrupted transfers omit desync, keep isolation asserted, then restart
through the public loader reset. They test two frame boundaries, not every
byte position, malformed headers, power interruption or hostile bitstreams.
The 256-vector cell test also passes in this run. Twenty Python tests pass
across frame decoding, reordering and the existing mapping audit; all four
experiment shell scripts pass syntax checks. The captured runner completed
while a later manifest-only change was made to the working script, covering
the runner snapshot fix without repeating the expensive builds.

## What remains before adopting it

- Extend interrupted/restarted-load coverage beyond the two tested frame
  boundaries, including partial words and configuration error handling.
- Extend beyond two LUT-only designs. This patch does not isolate DSP/RAM
  combinational paths, routing-only cycles, or every possible local path.
- Define a production sequence that parks external outputs and resets user
  state before releasing isolation. The test resets through the input pin
  after loading; it does not guarantee clean outputs throughout release.
- Measure CMOS5L area, timing and distribution skew. The source adds two
  clamps per LUT, 1,344 across the large 672-cell reference before synthesis
  optimization, plus the global hold net. This is a structural count, not
  an area estimate for the proposed small tapeout fabric.
- Integrate an accepted repair into the generator/architecture source and
  validate the resulting mapped netlist. Passing a modified RTL copy does
  not close the stock reference reload gate or phase 0 as a whole.

## Reproduce

Activate `.venv-fabric` and prepend OSS CAD Suite 2026-06-29 to PATH, then:

```bash
bash scripts/fabric_order.sh build/fabric-reference-warp-reference.OBUfXfus reverse
bash scripts/fabric_order.sh build/fabric-reference-warp-reference.OBUfXfus clear-columns
bash scripts/fabric_order.sh build/fabric-reference-warp-reference.OBUfXfus hold
bash scripts/fabric_order.sh build/fabric-reference-warp-reference.OBUfXfus hold validate
```

Use your actual cached reference build path. `validate` runs full A/B/A,
recovery after 33 and 199 frames of an interrupted second image, and the
wrong-image negative control. The default mode tests quick A/B/A and B/A/B.

The inspiration for clearing came from the pinned
[Tiny FABulous helper](https://github.com/mole99/tt-fabulous-ihp-26a/blob/4b284f528febbec39208d49a931b75ef63f1937b/tb/testcases/common.py).
Its implementation clears all columns through the parallel fabric interface;
our serialized per-column public-loader experiment is a distinct operation.

# LUT switch-pruning screen

This experiment records two LUT-tile switch-choice reductions screened on 2026-09-28. They are scratch candidates, not selected WARP architectures. `removed_pips.csv` removes 313 choices; `removed_pips_clock_protected.csv` removes 307 and preserves six global clock/reset/enable choices. The first full-fabric model used stale tile artifacts; session 18 regenerated the clock-protected 5 × 3 model from the exact 530-bit hardened tile, then rerouted three design-set examples with valid bitgen/frame checks. Direct functional configuration remains unproven, and the 4 × 3 and aggressive 5 × 3 routeability claims remain unverified. See `docs/WORKLOG.md` sessions 17–18.

Apply the same manifest to a disposable macro copy:

```sh
.venv/bin/python spikes/route_prune/apply_manifest.py \
  --pips macro/warp_g1/fabulous/.FABulous/pips.txt \
  --bel macro/warp_g1/fabulous/.FABulous/bel.txt \
  --fasm build/protocols/uart/design.fasm \
         build/protocols/spi_ctrl/design.fasm \
         build/protocols/i2c_ctrl/design.fasm \
  --output build/arch_explore/route_prune/pips.txt
```

The script verifies that none of the manifest choices is selected in the supplied FASM routes at a LUT tile, and removes the same choices from every `FABULOUS_LC` tile in the PIPs file. Use its output only in a disposable architecture copy. The timing delays used in the software screen are placeholders. Preserve ordinary G1 files and do not tune against held-out protocols.

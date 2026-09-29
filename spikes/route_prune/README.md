# LUT switch-pruning screen

This experiment records two LUT-tile switch-choice reductions screened on 2026-09-28. They are scratch architecture candidates, not selected WARP architectures. `removed_pips.csv` removes 313 choices; `removed_pips_clock_protected.csv` removes 307 and preserves six global clock/reset/enable choices that the more aggressive 5 × 3 screen needs for SPI routing. Three current design-set examples were successfully rerouted and bitgen-checked on the clock-protected 5 × 3 candidate. The earlier claim of identical FASM was invalid because the first software run used stale nominal-corner PIPs; see `docs/WORKLOG.md` session 17.

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

The script verifies that none of the manifest choices is selected in those FASM routes at a LUT tile, and removes the same choices from every `FABULOUS_LC` tile in the PIPs file. Use its output only in a disposable architecture copy. Full-fabric software models and feature maps were regenerated for the route screen, and three known workloads passed bitgen/frame checks. The timing PIPs used placeholder delays, and no dynamic fabric simulation or shell hardening was performed. Preserve ordinary G1 files and do not tune against held-out protocols.

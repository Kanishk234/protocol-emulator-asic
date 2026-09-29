# LUT switch-pruning screen

This experiment records a LUT-tile switch-choice reduction measured on 2026-09-28. It is a scratch architecture screen, not a selected WARP architecture. The exact 313-choice removal set is in `removed_pips.csv`; it was selected by examining unused LUT-tile switch choices and then validated against the UART, SPI-controller and I2C-controller design-set routes.

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

The script verifies that none of the manifest choices is selected in those FASM routes at a LUT tile, and removes the same choices from every `FABULOUS_LC` tile in the PIPs file. The caller must use the output only in a disposable architecture copy. The physical screen also required a regenerated LUT tile switch matrix and configuration-memory map. It did not regenerate or validate the full fabric's feature-to-bitstream mapping, and the protocol preservation evidence is limited to three currently routable design-set examples. Preserve all ordinary G1 architecture files and do not tune against held-out protocols.

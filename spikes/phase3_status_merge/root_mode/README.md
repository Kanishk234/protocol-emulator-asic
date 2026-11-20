# D-192 root-clock mode experiment

This patch is relative to D-192 candidate commit `76d8c829a30bf63362fcfb870168c9113de09d7f`. It changes only `src/trw_pin_cfg.v`. The expected patched RTL SHA-256 is `02a63f1d46ad7360a0f9a8a56b004478b629540ce4eb25234235b7b4b9c43581`.

The cached joint TX/RX mode predicate moves from a gated stage/latch pair to a root-clock register enabled by the same word-zero write. A word-zero write during reset still stores zero. The design continues to feed output levels back to receivers in the same clock. This trial tests clock insertion and hold repair effects on the failing launch path.

The archived differential Icarus fixture compared all configuration outputs at five points in each cycle. It passed 665,760 comparisons each for full and lean configurations, including all word-zero values with and without reset. Generic full-chip synthesis reduced the cell count by 102 while increasing maximum U0 mode to U2/U3 RX timer depth from 61 to 63 levels. These results do not establish physical improvement.

To reproduce the source, apply `root_mode.patch` in a clean copy of the specified candidate and compare the patched file hash. Retain its complete configuration, 8×4 geometry, and 20 ns clock. Compare pre-routing functional setup, fast hold, electrical checks, antenna, and congestion before proceeding to detailed route. Measure extracted setup and hold, especially the U0 launch route and the separate U0 token-producer endpoint, before considering adoption.

Icarus full pin-unit regression passed all 60 tests with the patch applied to the D-192 candidate. This is module-level RTL evidence.

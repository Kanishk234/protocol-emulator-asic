# Fixed-original-placement buffer experiment

[38101405271](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38101405271),
commit ed0b8bf, passes the placement and estimated electrical diagnostic in
2min16s including hosted setup. It does not run global/detailed routing,
extraction, configured timing or loaded native function.

The same ten identity buffers and six-load groups as37956470190 are inserted
into the same authenticated cluster8 checkpoint37811985079. Only legalization
policy changes: originals are temporarily immovable, then their original
statuses are restored. Native legality passes. All3596 original masters,
origins, orientations and statuses match; all18073 original terminal
connections match after contracting the ten buffers. Original movement is0,
compared with1550 moved cells in the preceding buffer trial. The fixed macro
remains exact. Original electrical limits and all three corners are retained.

| Explicit estimated corner | Baseline fanout failures | Candidate fanout / slew / capacitance failures | Candidate setup / hold slack (ns) |
|---|---:|---|---|
| fast1.32V−40C | 5 | 0 / 0 / 0 | 14.5141 / 0.116141 |
| slow1.08V125C | 5 | 0 / 0 / 0 | 12.7828 / 0.635476 |
| typical1.20V25C | 5 | 0 / 0 / 0 | 13.8665 / 0.304198 |

Six separate baseline/candidate STA processes provide the actual corner
coverage. Candidate setup and hold violation counts are0 throughout.
These use estimated shell parasitics with the fabric macro blackboxed;
the numbers do not establish extracted or configured-fabric timing.

Candidate ODB SHA256:
`0d2e6ea8666c9336e4447018be9325275f9366f58cb785cf6b70b616734b84e9`.
Candidate NL SHA256:
`3e3e9fd0a7632c1669858c99ff968aebcd671550488736f4c51c8d2222722136`,
identical to the preceding ten-buffer trial's connectivity.
Original SDC SHA256:
`2fd4e213532d83ee258899b6fc1ed48c4e5d91ddb0ccbe21eea0226cc90fd56e`.

The next comparison is strict native GRT on this candidate and the unchanged
cluster8 baseline, with identical original50-iteration routing policy. It can
measure the effect of avoiding incidental placement movement, but baseline
congestion and the dominant CRC/SPI/clock hotspot may remain. No successor
promotion, architecture advantage or operating-frequency claim follows.

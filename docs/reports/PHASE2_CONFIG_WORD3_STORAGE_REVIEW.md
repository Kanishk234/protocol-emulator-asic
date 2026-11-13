# Configuration word 3 storage review (2026-11-12)

Status: isolated local prototype; not selected for physical screening or integration.

The native-drive screen 43178099947 fails one antenna net at unit 1 configuration word 3 bit 3. The shorter-wire trial [43294055929](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/43294055929) instead fails two antenna nets/pins: the unit 1 word 3 gated clock and hold8181/A. Electrical violations and global-route overflow remain zero. Neither run qualifies for detailed routing.

The local prototype replaces stored word 3 bits with the existing root-clock IDLE-flop implementation. It retains write-qualified reset, staged writes, field encodings and restart behavior. It targets a general configuration-storage implementation issue, not protocol-specific hardware. No main RTL, SDC, project config or official workflow changes were made.

Evidence in `/tmp/tripwire-pinbank-ff` (temporary local output, not committed):

- FULL=0 phase-equivalence proof: 459 points proved, zero unproven; FULL=1: 558 points proved, zero unproven. These prove the configuration wrappers under their modeled clock phases, not the complete chip.
- Each configuration simulation passes 133,152 cycles and 665,760 phase comparisons, including all 65,536 word-3 data values under both reset states.
- A deliberately incorrect unconditional-reset implementation fails at cycle 173 after initialization, demonstrating that the comparison detects the relevant reset-semantic regression.
- Full 22-case L3 RTL replay passes: 22 passed, zero failed/skipped, 420.53 seconds. Optional sigrok annotations are disabled; protocol waveform/model checks remain active. This is RTL replay, not routed gate-level evidence.

Matched local full-chip mapping excludes NAND2_1 and NOR3_1 in both variants. It uses ideal clocks and no routed parasitics; these are not signoff timing results.

| Measurement | Reference | Word 3 flops |
|---|---:|---:|
| Mapped standard-cell area (µm²) | 411236.0280 | 413170.7832 |
| Typical flop slack (ns) | 10.629 | 10.319 |
| Typical SRAM slack (ns) | 11.561 | 11.782 |
| Slow flop slack (ns) | 5.614 | 5.137 |
| Slow SRAM slack (ns) | 6.557 | 6.968 |

Area increases about 0.47%; worst slow flop slack decreases 0.477 ns. The worst local launch remains unit 0 word 0 bit 1, rather than the changed word. Whole-chip synthesis remapping changes its logic chain. Removing a vulnerable gated-clock branch does not establish antenna closure: the new data muxes and clock loads also require physical validation.

Decision: do not launch a new hours-long screen solely on configuration equivalence. Retain the structural idea as a fallback and require a stronger timing/physical case before selecting it. The narrower PIN_N-only variant was also rejected after the measurements below; it retains the event-field latches and their word clock gate, so it does not solve the wire175 clock-gate offender. The best qualified extracted reference still fails slow setup by 1.982448 ns; Phase 2 remains open.


## Narrow PIN_N-only follow-up

Only the five selector bits per unit use the root-clock flops; event fields keep their prior implementation. Scratch evidence is in `/tmp/tripwire-pinn-ff`.

- FULL=0/1 phase proofs pass 461/560 equivalence points, zero unproven.
- Both exhaustive simulations pass 133,152 cycles / 665,760 phase checks.
- Mapped area: 411911.5896 µm², about +0.16% versus the matched reference.
- Typical flop/SRAM slack: 10.331 / 11.186 ns.
- Slow flop/SRAM slack: 5.053 / 5.927 ns; both regress versus the reference.

Do not launch this variant or spend another full protocol replay on it. Functional correctness alone does not justify physical screening when the cheap timing filter regresses. Both storage variants are rejected for now. A new setup candidate must target the mode-to-timer/control cone and be evaluated separately from native antenna repair. Root-clock storage is not shown to improve either routed setup or antenna closure.

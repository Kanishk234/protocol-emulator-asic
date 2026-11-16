# Parallel closure work — 2026-11-16

Scope: shorten the route from current native screen43920762758 to a real-design, unchanged official GDS run. No main hardware, template jobs, constraints or acceptance gates changed. No new physical run launched.

## Completed independent work

- Prepared an isolated review checkout at `/tmp/tripwire-owner-promotion-review` from main plus exact owner candidate RTL, candidate spec and reviewed full-design top-level test inputs. Generated files regenerated and generator check passes. RTL/header bytes match the screened owner source exactly.
- Packaged the eight pinned SRAM views with upstream Apache-2.0 LICENSE and per-file provenance. Hashes match the reviewed fixture manifest. This package needs no simulator-time SRAM download when the views exist. No macro assets copied to main.
- Isolated top-level RTL smoke passes4/4 (identity/time/SRAM, lane forwarding, full/lean UART and SRAM routine); this is not gate-level evidence.
- Added review-only input auditor: checks real-design source list, test/source-list synchronization, local macro/PDN availability, macro provenance, no external/absolute macro dependency, and unchanged official workflow bytes. Six focused positive/negative tests pass; input audit passes on the actual package. Always reports adoption/signoff false.
- Audit explicitly flags23 config fields outside the supplied AGENTS.md allowed-edit set. They require deliberate policy/config review before main adoption. Input completeness does not authorize these settings or prove physical portability.
- Checked official action tag at e7a50f8f46f9f8df4b2c9935bfeb1cbc6b6ae4f6: CMOS5L still selects LibreLane3.1.0.dev4. Current support-tools main8f7b5060d7f6df73bfd2e0b8d8fa0fd1dca0a0b1 is13commits ahead of the screen snapshot9d13ff3e3e6202090740110438c6a10c1d62ca0f. Compared files: product datasheet assets/workflow plus project_info.py extracting unchanged analog limit6 into a constant. No observed hardening-generator/technology/dependency change in this comparison; actual clean-checkout official execution remains required.

## Additional local timing experiment

Composed owner factoring with direct joint pad decode as a local backup, no physical launch. Mapped area415141.9398um2, slow global flop/SRAM reserve5.314/6.160ns, measured config-launch reserve5.615897ns. This regresses owner-only6.125/6.125ns and launch6.801030ns; reject. Individually equivalent changes are not guaranteed to improve timing when composed.

## Verification runner repair and in-progress checks

Fresh million-clock L2 comparison and L2-INJECT run on exact owner source. Initial injection attempt correctly stopped: old runner knew only the original lane-priority expression. Added exact reviewed shared-priority form, retaining ambiguity rejection, isolated builds, clean baselines and required scoreboard divergence. Twenty focused tests across promoted checks, input auditor and owner helper pass. Repaired priority negative control detected at clock99; cursor and million-clock completion remain pending until actual results are collected. See BUGS.md. Do not credit the older candidate's mutation evidence to this source.

## Highest-value remaining choices

1. Finish exact-source tests and clean-checkout/config review while the existing screen runs. This removes serial work after physical success.
2. If owner screen qualifies, spend the next physical run on that exact source. Measure extracted setup/hold, gate counts and paths; keep all final gates fixed. Do not assume its +0.684ns local cone gain covers -0.784ns routed failure.
3. If failure remains in pad feedback, target that measured cone with a general shared configuration decode/cache, only if it preserves live-write semantics and proves equivalent. Price added state/clock/hold cost first; don't register the live pad signal or add a protocol-specific shortcut.
4. If delay is predominantly inserted hold cells, consider a separate supported native hold-target experiment with unchanged hold acceptance. Analyze fast-corner exposure first; no manual buffer deletion and no speculative target relaxation.
5. Do not broaden placement/CTS sweeps or launch many unranked alternatives now. Reject local regressions early; protocol correctness alone does not justify physical testing.

Outstanding adoption gates: reconcile2lanes/4units/U0full contract; review config and macro packaging; refresh selected-source tests/mutations; final routed protocol replay with required decoders; unchanged official GDS, LVS/DRC/antenna/precheck/GL and main CI. Historical checked boxes do not qualify new source bytes. The previous one-off antenna-exception routing approval is not blanket authorization for another failed-screen route.

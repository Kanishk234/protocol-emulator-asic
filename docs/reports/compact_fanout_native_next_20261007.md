# Compact fanout and native mapping follow-up: 2026-10-07

The compact shell has same-layout native routing, Magic, KLayout and
GDS-based shell LVS closure in37669731197/37674839060. That does not qualify
the macro's native behavior or configured timing. Original physical LUT tile
netlists still fail loaded native simulation (BUG33). Regenerated
`original_control` and `mux_tree` mappings pass their bounded loaded UART
tests, but do not yet have matching physical views. No check is waived and
no successor is promoted by this report.

Latest stage diagnostic37708777882 fails all six cases before UART because
the stronger named-configuration audit finds14 unknown signals in the control
and12 in the two C2 substitutions. Actual latch bindings versus retained
aliases must be resolved before interpreting this as synthesis/physical
divergence. Latest corrected driver route37708459393 remains active at the
session68 status check; no fresh routed electrical result is available yet.

## Portable matched-tile hardening preparation

A bounded physical experiment should start from the exact passing C2 mapped
netlist in the table below, bypass synthesis, and preserve the original pin
geometry. Use a mounted Python API driver directly inside the pinned LibreLane
container. The standard dockerized wrapper does not support external plugins;
see the official [plugin documentation](https://librelane.readthedocs.io/en/stable/usage/writing_plugins.html)
and [custom sequential flows](https://librelane.readthedocs.io/en/stable/usage/writing_custom_flows.html).

Reuse the attributed, unmodified FABulous I/O-placement script and output-port
buffering adapter from plugin revision
`dcc038217472822330b33f61fadbc06e0c3cc96d`. Importing the whole old FABulousTile
flow would regenerate RTL and omit STA. The checkpoint alone lacks all the
pin/config/header inputs needed for faithful reproduction. Authenticate the
original `pins.yaml`, tile/common and resolved configs, JSON header, SDC and
final LEF/DEF before dispatch. Initial state must reference the candidate
netlist and its compatible header, never a leftover original netlist view.

Preserve C2 die190.08x196.56um, signal layers Metal2 through Metal4,
horizontal I/O Metal3/vertical I/O Metal2, original PDN/20 edge obstructions
and GRT adjustment0.3. First run only import/floorplan/I/O placement and
compare actual port names/directions/pin rectangles/power geometry. Launch
long routing only after that preflight and a valid native control pass.

The original tile uses CLOCK_PORT=null and removes every STA stage. Its
20ns configuration field therefore provides no setup/hold evidence.
Retain final mapped netlist and generated physical/parasitic/timing views,
configs, provenance and checker reports; retest the actual final netlist.
Configured timing still needs identified clocks, matched tiles and
configuration-specific path constraints in the composed fabric.

## Fanout is a pinned library limit

The authenticated slow-corner Liberty used by driver screen37688389888 is:

- Path: `ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib/sg13cmos5l_stdcell_slow_1p08V_125C.lib`.
- SHA256: `3ee222c580ba33acb2131ac2bf224ff8ee9700751835b73aaec72b670bb31d3c`.
- PDK revision: `2bbec755dc67ca3db0261c3d6163e15735d66710`.
- Upstream Git blob: `ad0f1a62beccbfd5c614803063e82e7d2613cb6e`.
- Header line31: `default_fanout_load : 1`.
- Header line36: `default_max_fanout : 8`.

The [pinned upstream file](https://github.com/IHP-GmbH/IHP-Open-PDK/blob/2bbec755dc67ca3db0261c3d6163e15735d66710/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib/sg13cmos5l_stdcell_slow_1p08V_125C.lib)
was verified through the GitHub contents API. The local cached library hash
matches `build/cloud_slew_37688389888/inputs.json` exactly.

The retained SDC has SHA256
`2fd4e213532d83ee258899b6fc1ed48c4e5d91ddb0ccbe21eea0226cc90fd56e`.
Its line105 says `set_max_fanout 10.0000 [current_design]`. That design limit
does not relax the stricter library8. The report's effective limit8 is
therefore supported by the actual supplied library, not a report artifact.

Evidence: [driver screen37688389888](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37688389888),
retained `baseline_checks.rpt` and `candidate_checks.rpt`. Their max-fanout
sections contain the same33 violations:

| Category | Violating outputs | Actual fanout | Effective limit |
|---|---:|---:|---:|
| Clock leaf buffers |27|13–22|8|
| Configuration distribution/state outputs |6|12 each|8|

The configuration outputs are
`u_cfg.g_col[1].u_col._23_/Y`, `u_cfg.g_col[2].u_col._23_/Y`,
`u_cfg.g_col[3].u_col._22_/Y`, `u_cfg.g_col[4].u_col._22_/Y`,
`u_cfg.g_col[5].u_col._22_/Y`, and `u_cfg.u_fsm._208_/Q`.
The in-memory `u_cfg._54_` driver resize removes the nine measured slew
violations in that same-wire diagnostic but leaves these33 fanout violations.
The routed resize experiment37690243797 is separate; its fresh extraction
and physical/electrical checks must be inspected independently.

## Bounded clock-tree preflight

After the current route experiment, obtain and authenticate the original
pre-CTS database, constraints and physical configuration. Run a cloud-only
CTS/legalization/parasitic-estimation preflight with only
`CTS_SINK_CLUSTERING_SIZE=8` changed. Keep the macro location, clock target,
library, buffer choices and all electrical/timing constraints. Do not append
a second tree to an already routed/post-CTS database.

[OpenROAD CTS](https://openroad.readthedocs.io/en/latest/main/src/cts/README.html)
documents explicit sink-cluster sizing. The pinned LibreLane CTS script must
be checked for the corresponding supported flag before execution. A nominal
cluster size is not acceptance: count actual loads on every resulting clock
driver, including dummy loads and any later additions. Require actual fanout
at or below8, legal placement, unchanged logical connectivity, and report
clock skew, setup/hold paths, slew and capacitance. Estimated parasitics do
not qualify postroute timing.

Use a standard hosted runner and a bounded stage cap; do not launch a whole
chip route until the preflight shows a useful legal candidate. Additional
clock buffers cost area, wire resources and clock power and can alter hold
and skew. Measure these costs. Configuration fanout requires a separate
distribution-buffer experiment; fixing clock clustering does not clear its
six violations. Do not increase constraints or suppress the reported checks.

## Exact recovered native stage inputs

Known passing regenerated original-control evidence is
[37659171115](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37659171115).
Its artifact has `manifest.json`, five candidate tile netlists and three
strict loaded-test XMLs. RTL control, mapped native and USER_RESET each pass
the28-TX/28-RX UART stress under the documented D-023 harness. This is
functional mapping evidence, not matching layout/SDF qualification.

| Tile | Passing regenerated SHA256 | Original physical final SHA256 |
|---|---|---|
|`LUT4x8_ha`|`4425946a3e9f56218b04e1af883573df59fe8654f4333941190d61e576ffc8fc`|`5dd10b73b5082cd65365f47e6a5ee616aac5fec1b2bdedb8adfc5b84a562650f`|
|`LUT4x8_ha_C2`|`03c21b8e400e1774390e67b0939422959d37e26849adca18fa082f492cf5cdaf`|`e0aef98643db5a98650e7bc6401de5db72731e89457aae3fd9962ae39b6c6f8c`|
|`LUT4x8_ha_C3`|`b0309fa92157ba537a669b04281f7c7a482d5461c151b66c57267f79cf47895f`|`36cc961d9cefb51fd7546eac251f75c18ea792d0f023c59964386ea0f343cd2c`|
|`LUT4x8_ha_C4`|`b76ddf0c19dae3494f7db35d678a85e81550d35ebf05e678b2c37a7afad2a8b9`|`acf7ce4001e9206af349b0252a873877b9b86da39db891cec6e03fc6b43f1ecd`|
|`LUT4x8_ha_C5`|`6553e1c9c307956a2780161ef8d67fadb8c1baaa91427876c9f16e6f088577c0`|`c04e339403b0f0d59507fc39f6d7b78fe8979be6bb212ad696507d859f8eedd1`|

Four local original hardening runs retain synthesis outputs whose own final
netlists exactly match the authenticated original physical hashes above.
Their common path prefix is
`build/arch_explore/tiles_5x3_phase/fabulous-tiles/tiles/tiny/`.
The complete synthesis path is
`<prefix><tile>/runs/<run>/06-yosys-synthesis/<tile>.nl.v`.
The corresponding original final path is
`<prefix><tile>/runs/<run>/final/nl/<tile>.nl.v`.

| Tile | Run directory | Synthesis SHA256 |
|---|---|---|
|`LUT4x8_ha_C2`|`RUN_2026-09-29_17-38-37`|`2c9faa6dc332004212c2719a8ca740b902d8c720f5f7da664007d3df7eedf6d9`|
|`LUT4x8_ha_C3`|`RUN_2026-09-29_17-42-30`|`26288c095ae02dfccac19c0e805bb52779e0bb1157b0b057031a296896c2dd90`|
|`LUT4x8_ha_C4`|`RUN_2026-09-29_17-48-56`|`ea5a830b9a9ac834c9ebbff680cc594d39c5a6e82e76fde544561945a98bb94c`|
|`LUT4x8_ha_C5`|`RUN_2026-09-29_17-54-53`|`3ee5180eda0869456ce7f41695dc75ef1afd50be745896858551a98b2e73b8d2`|

A hash-matched base `LUT4x8_ha` synthesis run was not recovered in this audit.
Nearby older base-tile runs have different final hashes and must not be
represented as that authenticated source. Local ignored build paths are
diagnostic input locations, not committed reproducibility artifacts; the
cloud workflow must receive explicit authenticated inputs.

## Native diagnostic sequence before more hardening

1. Copy the compact experiment; install all five authenticated passing
   `original_control` netlists and rerun the loaded native stress/reset control.
   Preserve the original inputs, real SPI loader and runtime configuration.
2. On separate copies of that passing baseline, replace only C2 with its
   original synthesis-stage netlist, then only C2 with its original final
   netlist. Record every source/candidate hash and strict non-skipped XMLs.
   Do not combine C2–C5 changes into the first experiment.
3. A synthesis-pass/final-fail result localizes a physical-flow transformation
   for C2; both failing implicates the earlier mapping or its simulation
   behavior. Both passing means the actual failing combination/type remains
   to be isolated. Do not assume C2 alone must reproduce BUG33.
4. Repeat other recovered types only as needed, then harden one verified
   original-control mapped tile from an authenticated `nl` initial state,
   starting at floorplanning so resynthesis cannot silently replace the
   tested mapping. Keep the original footprint, pins and clock target.
   Retain actual final netlists and matching physical/timing views; retest
   that final netlist before expanding to all five types and restitching.

This stage comparison costs bounded hosted simulation, not another full
hardening. The existing native runner uses600s per simulation; select smoke
coverage for initial localization if a job bound cannot contain all stress
and reset cases, and report that reduced scope explicitly. A newly hardened
tile costs routing time, area and possible pin/timing changes and therefore
needs its own measured physical acceptance. A one-tile substitution into an
otherwise resynthesized fabric remains a limited integration test; it does
not give physical qualification to the other four netlists.

The existing primitive mux proof and captured-configuration constant proofs
do not establish full sequential or four-state tile equivalence. Original
native failures, configured timing, fanout and complete successor acceptance
remain open. This audit ran only lightweight reads/hashes; no local EDA,
workflow dispatch or upstream modification.

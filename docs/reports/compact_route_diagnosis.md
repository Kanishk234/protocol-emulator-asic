# Compact routing diagnosis from completed snapshots

Date: 2026-10-05. Read-only inspection while the original routes continue.
No active input, database, configuration or upstream tool was changed.

The CRC experiment reduces shell duplication; it is not an established root
cause. Antenna violations and ordinary short/spacing markers are separate
checks, although antenna repair can change routing and move DRC hotspots.

## Ordinary DRC: west-channel concentration

Lead run: `compact_narrow_rows_drt_20261005`,
`01-openroad-detailedrouting/drt-run-2/tt_um_warp.drc-16.rpt`.
The completed second antenna-repair pass contains 576 markers: 477 Metal2,
88 Metal3, 11 Metal4; 392 shorts and 184 spacing markers. All centers are
west of the macro. 379 centers lie at x=0–50, y=500–550 µm.
These are marker incidences, not independent electrical failures.

Saved OpenDB endpoints identify contributors rather than guessed net names:

| Net | Driver / connection | Diagnostic implication |
|---|---|---|
| `net53`, 57 marker incidences | `fanout53` driven by `net54`, then `net60`, then `u_shell.u_crc._078_` | CRC-associated buffered distribution crosses the dense west region |
| `net143`, 39 | `fanout143`, input `u_shell.u_spi._097_` | SPI receiver-related distribution is also involved |
| `net1112`, 27 | `hold1113`, input `u_shell.cmd[2]` | Hold-repair routing of a command bit contributes |
| `net722`, 26 | SPI-instance tie-high cell | Even constant distribution appears in marker pairs |

An audit of instances whose lower-left lies in the 50 × 50 µm hotspot finds
206 instances, 88 within `u_shell.u_crc`, and one antenna diode. Their summed
cell area is 2,320.6176 µm²; this is not an exact regional utilization because
cells may extend beyond the bin. The evidence supports investigating local
pin/wire demand and buffer placement, not blaming only CRC or local diodes.

Shared CRC run: `shared_crc_full_drt_20261005`, first-pass iteration 6.
673 markers: 464 Metal2, 181 Metal3, 28 Metal4, all west. Dominant bins are
x=0–50,y=300–350 (257) and x=0–50,y=250–300 (240), then
x=50–100,y=300–350 (138). Named contributors include `u_shell.cmd[0]`,
`u_shell.cmd[4]`, `u_shell.cmd[1]`, `u_shell.u_crc.word_valid`, and byte data.
These are different stages of different runs; do not infer a final winner.
The changed hotspot suggests congestion has moved, not disappeared.

## Antenna: exact nets and ratios

Read-only `check_antennas -verbose` on completed routed databases reproduces
the flow's antenna counts. Inspecting LEF antenna data needs no liberty timing
claims; these results are from OpenROAD's routed-wire checker.

| Saved lead pass | Violating net | Pins / layer | Cumulative area ratio / limit |
|---|---|---|---|
| Initial DRT (`drt-run-0/tt_um_warp.odb`) | `u_cfg.frame_address[28]` | columns 3/4, Metal3 | 255.18 and 251.08 / 200 |
| After repair 2 (`drt-run-2/tt_um_warp.odb`) | `net22` | three column-6 decode inputs plus `fanout21/A`, Metal3 | 203.25, 201.56, 203.07, 201.67 / 200 |

`net22` is driven by `fanout22`, input `u_cfg.frame_idx[1]`, at x=160.32,
y=3.78 µm. Loads include x=72.96, 678.72 and 1140–1154.88 µm. This is a
long configuration-index distribution route, distinct from the west CRC
hotspot. The repair-2 snapshot contains 16 diodes on `net27` (a buffered branch of
`frame_idx[0]`). The active third repair logs another 16 inserted diodes, but
its completed database has not been audited yet; do not assign those diodes
to a net from the earlier snapshot. The detailed checker and repair's global
estimate need not identify identical offending branches.

Between initial DRT and repair 2, total diode count rises from 21 to 51,
while west-channel diode count remains 21 and the hotspot retains one diode.
Thus increased west DRC cannot be attributed simply to extra west diodes.
The flow reroutes after repair. Causal attribution between repair, modified
guides, legalizing and rerouting still needs an isolated experiment.

The pinned LibreLane `drt.tcl` runs the configured 16 optimization iterations,
then checks/repairs antennas and reroutes up to three times. That explains
repeated iterations and why an early DRC improvement is not the final result.
This is upstream code inspected in place, not modified.

## Next isolated experiments

1. Target long configuration-index distribution: examine grouped local
   buffering/branch placement so distant column loads do not share a long
   unprotected route. Preserve exact decoding, clock/reset, configuration
   hold/setup and dynamic bit loading. Verify all real loaded bits afterward.
2. Compare the flow's supported jumper-only antenna repair mode against
   default repair from the same preserved pre-DRT database. First establish
   this pinned router actually supports it; do not disable antenna checking
   or treat fewer DRC markers as signoff. Do not launch another expensive
   full route while existing jobs occupy the machine.
3. For the west hotspot, investigate targeted placement spreading or local
   routing-resource reservation, using saved pin locations and hold/fanout
   trees. Change one control at a time and retain the same macro, clock and
   hold margin. Broad density/padding screens already failed; do not repeat
   them as though they are new fixes.

These are test hypotheses, not proven fixes. Neither active candidate has
completed physical/timing signoff or native mapped-fabric protocol simulation.

## Reproduce inspection

Use the pinned OpenROAD binary and the project venv for report parsing:

```sh
WARP_AUDIT_ANTENNAS=1 WARP_ROUTE_SNAPSHOT=/absolute/path/to/completed.odb \
  openroad -exit spikes/compact_edges/inspect_route.tcl > build/route_audit.log
source .venv/bin/activate
python spikes/compact_edges/report_drc.py /absolute/path/to/native.rpt \
  --macro-bbox 121.44 15.12 1241.76 691.74
```

Read completed snapshots only. The script never saves a database. Evidence
under `build/arch_explore/compact_edges/`: `lead_pass2_iter16_summary_20261005.json`,
`shared_crc_iter6_summary_20261005.json`, `lead_pass{0,2}_db_audit_20261005.tsv`,
and `lead_pass{0,2}_antenna_audit_20261005.log`.

Primary references: [OpenROAD antenna checker](https://openroad.readthedocs.io/en/latest/main/src/ant/README.html),
[global routing and antenna repair](https://openroad.readthedocs.io/en/latest/main/src/grt/README.html).
Installed pinned code/logs establish behavior here; latest documentation may
describe capabilities different from the pinned version.

## Tighter macro: completed routing failure, 2026-10-05

D-040 shared CRC/local branches with the 669.06 µm macro finishes its stock
routing/antenna sequence at **144 DRC markers and zero antenna nets/pins**.
This is a routing failure, despite successful antenna repair. Native final
report: `compact_edges_tighter/chip_shared_crc_cfgbranches/runs/compact_local_route/04-openroad-detailedrouting/drt-run-1/tt_um_warp.drc-16.rpt`
under `build/arch_explore/`. Summary:
`compact_edges_tighter/pass1_iter16_summary_20261005.json`.
All markers are west of the macro: 141 Metal2, three Metal3; 86 shorts and
58 spacing markers. The 50 µm bins at (0,300) and (0,500) contain 74 and
40 markers. These are marker counts, not independent defects.

A read-only final database audit identifies the implicated clock trunk as
one buffer driving eight clock buffers spread over y=143.64–589.68 µm.
CRC bit 2 instead has three nearby loads at x=16.8–38.4, y=472.5–510.3 µm,
with its driver at (13.92,532.98). Another hotspot net, net1233, is a
hold-delay output sourced from configuration word bit 21. Thus remaining
violations include both clock distribution and local shell wiring; zero
antenna does not solve west-channel routing congestion. Audit:
`compact_edges_tighter/final144_net_audit_20261005.log`.
`WARP_AUDIT_NETS` now selects exact nets, including escaped bus names.

The original lead's failed 716-marker flow and this 144-marker flow were
stopped during subsequent incompatible Magic processing. Reports and
snapshots are retained. No successful flow was cancelled. The preplaced
configuration-diode experiment remains active in a separate directory;
its final antenna/DRC result is still unknown. Do not launch another full
route merely because its early marker count changes.

## Clock-layer locality screen (D-042)

A one-variable screen copies the baseline's exact pre-GRT state/config and
sets `RT_CLOCK_MIN_LAYER=Metal3`, retaining the same macro/clock/cells/placement.
Directory: `build/arch_explore/compact_edges_tighter/chip_clock_m3_screen/`.
Run `clock_m3_grt` completes: zero overflow,276156µm estimated wirelength
versus baseline276069µm;3497 cells and805813.14µm² complete cell/macro area in
both logs. This has no measured DRT/timing benefit yet. Clock guides may still
need lower-layer pin-access segments. Higher layers/vias have their own costs.
The active diode route uses separate, unchanged inputs. Research and installed
flow support: OpenROAD's linked GRT routing-layer documentation and pinned
LibreLane `common/set_routing_layers.tcl`. A second full route is deferred
until a justified same-stage comparison can be made.

Completed bounded DRT run `clock_m3_drt_screen`:3784 native markers at
optimization2 versus3482baseline; optimization1 was also worse3837versus3441.
Wall time13m08s. No full route is justified by this result; set this hypothesis
aside. Antenna repair and downstream checkers were outside this bounded
diagnostic, so its "Flow complete" message is not a passing chip.
Native summary: `clock_m3_iter2_summary_20261005.json` under the tighter root.

## Local CRC spacing screen (D-043)

The largest exact final baseline pair (`net37`, `u_shell.crc[2]`) involves
12unique cells and20markers. `pad_crc_hotspot.tcl` reserves two sites per
side around these cells in a copied pre-GRT database. The installed legalizer
has no incremental flag. An initial four-site probe could not legalize one
CRC cell within the requested20µm per-axis bound. A two-site unrestricted
probe legalized but moved1539cells, so it was not routed. The retained probe
temporarily anchors3055remote cells during legalization, restores their
original placement statuses afterward, and moves256cells in the CRC
neighborhood. Exact instance/master/net connectivity and all anchored
locations are checked. The macro stays fixed. This is not merely movement
of the12padded cells; neighboring clock/hold cells also move.

Directory `chip_crc_padding_local_screen`, run `crc_padding_grt`:0overflow,
277632µm estimated wirelength versus276069baseline,3497cells and805813.14µm²
complete instance area unchanged. The requested displacement cap is a tool
setting, not a measured strict movement guarantee; the origin-based maximum
Manhattan change is25.68µm. A bounded two-optimization DRT comparison is active
as `crc_padding_drt_screen`. Its separate `config_screen.json` disables only
post-DRT antenna repair for comparison; original stock config is retained.
No full routing/timing improvement or promotion yet. Source reference:
[OpenROAD instance padding](https://openroad.readthedocs.io/en/latest/main/src/dpl/README.html),
checked against pinned command help.

The ongoing D-041 diode route remains unchanged. Its optimization10 native
report has245markers, allwest (164Metal2/66Metal3/15Metal4), versus302at the
same baseline stage. Most now cluster at y250–350µm around shell-control
nets, not the baseline CRC pair. This is intermediate progress, not antenna
or final DRC success. Saved summary: `diodes_iter10_summary_20261005.json`.

## Completed results, October6

D-041 stock restart finishes detailed routing at258markers and0antenna
nets/pins. Its successive pass totals are101→198→258markers, taking66m00s,
43m58s and64m53s (174m51s total DRT wall time). The routing checker explicitly
fails. Later incompatible Magic processing was stopped via the owning exec
session, preserving reports. This is worse than the completed144-marker
baseline and is not selected. Native final summary:
`diodes_final258_summary_20261006.json` under the tighter root.

All258markers remain west:210Metal2,43Metal3,5Metal4;179shorts and79spacing.
The50µm hotspot bin at(50,250) contains153markers; the CRC area is no longer
the final hotspot. Read-only `diodes_final_control_audit_20261006.log`
identifies the50-marker-incidence `_0118_` as an inverter driving two nearby
NOR cells aroundy294.84µm. `net179` is a buffered RX-byte bit5 branch with
eight loads spanningy230.58–321.30µm. `rx_empty` crosses fromy177.66µm to
three shell-control loads at294.84–313.74µm. These are local access and
distribution hypotheses, not proof that more buffering fixes them.
Post-route STA has zero reported setup/hold violations at its modeled
corners, but the macro is black-boxed; this is not full-fabric timing signoff.

D-043 CRC padding diagnostic finishes13m22s at3477markers after two
optimizations versus3482baseline, while its first iteration worsens
4105versus3441. A five-marker final difference is insufficient to justify
another full route. No padding variant is selected. The12padded endpoints
retain their new positions at actual DRT input (`placement_survival.txt`).
Summary: `padding_iter2_summary_20261006.json`. All physical promotion gates
remain open, and frozen G1 stays the fallback.

Independent native mapped-fabric probe now runs with a corrected copied
wrapper source list: `compact_edges/native_cone_probe_session51.log` and
`simulation_chip_native_cone_probe_20261005_mapped_fabric/test.log`.
All8707exposed configuration bits still match SPI-loaded data with no
unknowns. Selected LB flop's unknown D cone reaches unknown neighboring
route inputs and flop feedback; its reset-selection mux chooses the data
path at the sampled pre-RUN point. The UART test still fails. This narrows
the next route/reset/initial-state investigation but does not establish
either a synthesis bug or a simulation-only cause. No state was forced.

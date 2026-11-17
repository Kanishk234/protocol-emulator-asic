# Exact qualified-screen continuation

Source screen [44017640255](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/44017640255)
passes all gates at e04f800d2ab1701cd97ff801e464830054b2b145. Independent local
review matches GitHub identity, full RTL/macro inputs, exact config and container,
raw timing/electrical/antenna reports, six fresh netlist exports and view hashes.
Review receipt: cache_final_antenna/artifact_review_44017640255.json.

- Project config:0b7a388f659ae287b20580fbfa0572b36809df2fd04b63988c5499f3b66598bc.
- Physical DB:b78055c7400228ff1e7b94808bbd71c490e9587cbd29c83beb1a69c5134ce74e.
- Setup reserve fast/typical/slow:+12.572991/+8.975251/+2.784036ns.
- Stock hold:+.102192/+.294138/+.614901ns; electrical/antenna0.
- Routing evidence remains explicitly the preceding zero-overflow full route
  plus native congestion-prohibited incremental antenna repair.

## Prepared continuation
Manual-only gds-cache-final-route-extracted uses separate routing and extraction
jobs. Restore the exact successful screen and repeat independent saved gates,
then fresh antenna0 and all-corner stock timing/electrical/functional checks.
No initial-antenna exception or additional resizer/global-route pass is allowed.
Continue only with the stock DetailedRouting step. Require completed state,
fresh raw and state route DRC0, unchanged existing logic/connections and only
allowed antenna additions before writing a route-completion receipt.

Extraction depends on routing success and binds source identity, workflow ID,
routed DB/netlist hashes and DRC0. It runs the existing native RCX/STA/checker
sequence with explicit stock constraints (0.25ns uncertainty), never the legacy
0.10ns hold override. Preserve effective constraint identity and verify fresh
max/min reports at every corner. Also generate real functional setup reports
through the pinned STA_EXTRA_CORNER_TCL_FILE interface, confirmed in dev4's
shared sta/corner.tcl.

The extracted gate mirrors and strengthens the current green screen criteria:
ordinary setup/hold nonnegative, fast hold at least50ps, zero setup/hold violation
counts, strictly positive actual flop/output setup reserve, unchanged endpoint
inventory, electrical0 and antenna0. Aggregate setupWS0from latch reporting is
not labeled positive headroom; actual positive reserve is checked separately.
This changes no SDC limit and waives no negative endpoint. Historical diagnostic
results and their older gate behavior remain unchanged.

135focused checks pass, all embedded Python/bash validates and the actual frozen
source passes independent inspection. Default historical extraction behavior is
retained; the new route explicitly selects stock constraints and functional
reporting. No official workflow, main hardware, clock or resource change. Native
execution pending. After a routed/extracted pass: full routed protocol replay,
reviewed source/config integration, then unchanged official GDS/precheck. Phase2
is not complete.

## Routed and stock-extracted result44031468510
Both jobs pass at c5824b6ba259155a312a92a8fa545d8319e1e9a9. DRT completion
checks fresh raw/state DRC0and original connectivity. Extracted gate reports
qualified=true/failures=[], all timing-violation counts0, electrical0 and antenna0.
At stock0.25ns uncertainty, functional setup fast/typical/slow is
+11.807575/+7.647178/+0.163304ns; hold+.150773287/+.391302668/+.742154359ns.
Ordinary aggregate setupWS0is retained and not called positive reserve.

Artifact14311359993(cache-final-drtroute-44031468510,149529385bytes) and
14313125675(cache-final-extracted-44031468510,144211986bytes) independently
reviewed: exact hashes, raw reports, constraints and logical conservation pass. The slow setup reserve is only163ps, so source/config/tool
parity matters during main adoption and official hardening. Full routed protocol
replay, official GDS/precheck and Phase2 completion remain outstanding.


## Full routed protocol replay44123392388 passes
All four groups and aggregation pass on1c9a278. Downloaded combined XML was
independently checked:22 unique expected cases, each with positive simulated time,
no failure/error/skipped entries. Netlist SHA537f41adee4320df81a0b7e907f011510cc578ab3c2a17105e00a80e0bacbcc9
is the exact post-fill netlist used for extracted STA. Exact PDK89d42ee, frozen
SRAM models, Icarus13, required sigrok and generated2-lane/4-unit tables are
recorded in protocol_result_44123392388.json. This is functional gate-level
simulation, not SDF-annotated simulation, official GDS signoff or silicon evidence.

An isolated integration checkout is prepared locally; generated files match the
frozen source and project config hash0b7a388f... is preserved. Main is still the
placeholder-selected design. Before publication:
1. Adopt matching2/4 spec/software tables, exact selected RTL/config/PDN/SRAM views
   and real pinout/source list; keep test/Makefile source list synchronized.
2. Replace counter-placeholder tests with real top-port host/protocol checks;
   provide matching SRAM models to RTL and official gate-level simulation.
3. Review two integration lint warnings (bounded integer comparison at
   trw_pin_io.v:48 and unused car_out_on at trw_pin_tx.v:162), preserving proven
   source identity where possible; then run generated-file/lint/regression checks.
4. Confirm macro redistribution provenance/licenses and official-tool input parity.
5. Publish coherent integration and run unchanged official GDS/precheck/GL/viewer.

No Phase2 completion claim: the official full-design run remains outstanding,
and extracted slow setup reserve is only163ps.

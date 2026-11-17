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

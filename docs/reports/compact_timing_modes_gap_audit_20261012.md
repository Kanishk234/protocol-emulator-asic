# Complete timing obligations for the compact successor

The next goal is timing on one matched physical chip. Current reports cannot be
combined into that claim. Actual C2 run38164099529 times programmed UART paths
at two positions/three libraries using that tile's own nominal SPEF. It retains
20ns period,.25ns uncertainty,.15ns transition and.95/1.05 derating. It reports
152inputs without I/O delays,529unclocked configuration latch pins and677/679
unconstrained endpoints. The four unannotated drivers independently have zero
loads in this exact tile graph. These observations have different implications:
zero-load omissions are resolved; loading, boundary timing and whole-chip skew
remain open. See compact_c2_delay_extracted_20261011.md for hashes/actual slacks.

| Mode / path class | Evidence available | Required next evidence |
|---|---|---|
| RUN: shell registers | Estimated six-corner guard pairs on current placement | Same routed layout extraction and setup/hold/electrical checks |
| RUN: C2 internal UART |38164099529 conditional examined paths | Integrate actual shell/global clock arrivals; keep user state dynamic |
| RUN: intertile and primitive paths | Other tiles are regenerated functional controls | Matched physical/netlist views for every tile, routed boundary paths and actual primitive clocks |
| RUN: selected configuration | Case analysis fixes exact loaded config bits | Authenticate each compiled image; qualify active data paths per image, including combinational pin paths |
| LOAD: configuration writes | Functional loading passes; selected RUN timing fixes configuration | Actual top-clock-to-config-data/strobe paths, latch enables and pulse widths; no stationary-config assumption in this mode |
| RESET/STOP/control | Pin parking/recovery simulation and bounded properties | Synchronous reset/recovery path timing and control propagation on matched layout, relevant transition modes |
| External host SPI | Contract SCK<=clk/8, CS setup8clocks/idle4 | Top-port constraints/CDC interpretation tied to real input synchronization and chosen host service contract |
| User external pins | Registered outputs/two-flop synchronized inputs | Explicit intended external timing contract, applicable min/max delays and pad assumptions; do not invent board budgets |

## Concrete order of execution

1. Finish electrical-clean shell native routing on a single placement. Retain
its exact ODB/netlist/SDC, extracted parasitics and unchanged margin policy.
Reject the fanout35 regression38178351037 (143vs133control). Physical layout
and estimated shell timing are distinct gates.
2. Build an authenticated inventory for that chip: each tile's physical
netlist/LEF/GDS/SPEF hash and placement, compiler graph/image hashes, and real
clock connectivity from topclk through shell/global buffers to user registers.
The successful C2 physical input is available as38114298036; all other tile
views must be matched, rather than inheriting regenerated-model behavior.
3. Execute separate RUN and LOAD coverage diagnostics on those views. Retain
`report_clock_properties`, `report_clock_latency`, `check_setup -verbose
-unconstrained_endpoints -multiple_clock -no_clock -no_input_delay -loops
-generated_clocks`, annotation reports and full min/max path reports. Classify
remaining endpoints by actual pin/connectivity and mode. An unconstrained
endpoint is not timed merely because a different register pair has slack.
4. RUN may fix authenticated configuration bits for a selected user image;
LOAD must retain configuration storage/control dynamics. Propagate actual
clocks; derive any latch-enable/generated-clock relationship from implemented
clocking and the loader contract. Setting cfg pins constant in LOAD, inventing
boundary clocks or cutting loops to obtain a pass is not acceptable.
5. Require complete required-path coverage and setup/hold/electrical gates at
specified PVT/RC conditions, then check additional compiled programs separately.
Three library corners on one nominal SPEF do not establish all RC corners or
all possible programs. Compiler Fmax remains an estimate until cross-checked.

The immediately executable check after routing is a coverage inventory on the
matched top-level clock/network, before timing optimization. Fail closed on
unknown/missing active clocks, missing required I/O contracts, absent parasitic
views or unmatched tiles. The existing conditionalC2 scripts are useful inputs,
but reusing their boundary-clock/stationary-config assumptions as a whole-chip
LOAD pass would conceal the remaining work. No architecture change, constraint
waiver, new clock target or sign-off claim is made by this audit.

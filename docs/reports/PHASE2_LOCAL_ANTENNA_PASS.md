# Passing bounded local antenna screen

Run [41979402848](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/41979402848), source6e5da2e, passes the edited and unchanged-control jobs. The edited full-design checkpoint passes every required pre-routing diagnostic gate together: setupWS0ns all three corners; hold fast/typical/slow+0.144394/+0.355043/+0.738651ns; slew/cap/fanout0allcorners; fresh antenna0nets/0pins; globaloverflow0withlive demand309924. Setup0isnonnegative, not positive setup headroom.

Independent artifact checks match all repeated raw corner metrics, fresh antenna and native congestion reports. Fresh ODB netlist readback contains exactly the three approved master changes plus one diode at hold7969/A, preserving every original signal connection. All unrelated placement is identical. Only fanout295andwire13568move/reorient within allowed set. Only _07219_,_10511_,net295change global segment geometry; all other45054routes remain identical.

Changes:wire13568BUF2→BUF8,wire12579BUF2→BUF4,_38673_NAND2_1→NAND2_2andone local diode. Bounded incremental routing avoids the previous broad legalization/global-reroute regression. The unchanged control reproduces reference timing and four antennas.

The original geometry_result.json uses a comparison without an allowed-net list, so its unexpected_changed_nets field includes the three permitted edits. The runtime gate separately checks the exact allowed set. Independent comparison with the declared set confirms all unrelated routes are preserved. Corrected future receipt formatting records this explicitly; no acceptance gate changed.

This is a passing local physical screen on the full design, not a clean stock-source reproduction or official GDS result. Diagnostic edits/extra steps cannot simply be copied into template jobs. No DRT, extraction, final-netlist protocol replay, LVS/DRC/precheck or phase completion follows from this screen alone.

Next: preserve and hash-bind the exact edited ODB/DEF/fresh NL and constraints for DRT/extracted validation; separately determine a permitted source/config recipe reproducing the repair with the unchanged official workflow. Do not modify main hardware or tick Phase2exit boxes based on this diagnostic. Evidence:spikes/phase2_stock_flow/local_antenna_pass_41979402848.json.

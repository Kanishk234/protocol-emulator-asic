# TRIPWIRE R2 (branch spike/r2-latch, DECISIONS D-032): constraints for sign-off STA.
# Exactly LibreLane's default. It is set explicitly because, without SIGNOFF_SDC_FILE, sign-off
# would reuse PNR_SDC_FILE (pnr.sdc) and lose the latch setup check.
#
# R4 run 7 (DECISIONS D-056, proposed): hold uncertainty 0.10 ns instead of the default 0.25 ns (setup keeps 0.25).
# After CTS the flow times with the propagated clock tree, so skew is modelled; clock jitter does not affect hold
# (launch and capture are the same edge). At 0.25 ns almost every short path fails hold at the fast corner by a
# few tens of ps (run 5's post-CTS netlist: 1,546 endpoints, median -0.05 ns), and the resizer spent ~50K um2 of
# delay cells on them in run 6. At 0.10 ns: 29 violations. The same value is used at sign-off.
source $::env(SCRIPTS_DIR)/base.sdc
set_clock_uncertainty -hold 0.10 [all_clocks]

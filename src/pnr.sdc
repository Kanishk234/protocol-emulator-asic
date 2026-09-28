# TRIPWIRE R2 (branch spike/r2-latch, DECISIONS D-032): constraints for the place-and-route steps.
#
# LibreLane's default constraints, plus one exception for the latch slot array (trw_slots):
# no SETUP repair on latch data pins. Those pins are written from a posedge flop (wdata_q) while
# the latch is transparent in the high phase, so STA reports them as borrowing time with a slack
# of exactly 0.000. LibreLane's post-CTS resizer demands +0.05 ns (PL_RESIZER_SETUP_SLACK_MARGIN),
# counts all 700 as violations and iterates without effect: 3 h 21 min in gds run 35962617201.
# Hold on those pins is still repaired. Sign-off STA uses signoff.sdc (the plain default), so the
# latch setup/borrow check is still reported at sign-off.
#
# R4 run 7 (DECISIONS D-056, proposed): hold uncertainty 0.10 ns instead of the default 0.25 ns (setup keeps 0.25).
# After CTS the flow times with the propagated clock tree, so skew is modelled; clock jitter does not affect hold
# (launch and capture are the same edge). At 0.25 ns almost every short path fails hold at the fast corner by a
# few tens of ps (run 5's post-CTS netlist: 1,546 endpoints, median -0.05 ns), and the resizer spent ~50K um2 of
# delay cells on them in run 6. At 0.10 ns: 29 violations. The same value is used at sign-off.
source $::env(SCRIPTS_DIR)/base.sdc
set_clock_uncertainty -hold 0.10 [all_clocks]

set_false_path -setup -to [all_registers -level_sensitive -data_pins]

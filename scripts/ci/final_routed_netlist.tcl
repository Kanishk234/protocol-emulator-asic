# Read-only final database netlist export; timing claims use extracted STA reports.
write_verilog [file join $::env(STEP_DIR) final_routed.nl.v]
write_verilog -include_pwr_gnd [file join $::env(STEP_DIR) final_routed.pnl.v]

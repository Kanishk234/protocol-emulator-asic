# D-054: pin-access feasibility only, no signal routing or acceptance waiver.
read_db $::env(WARP_PIN_SOURCE)
set_thread_count 4
set_routing_layers -signal Metal1-Metal4
puts "WARP_PIN native Metal1 via containment screen; no routing"
pin_access -via_access_layer Metal1 -via_in_pin_bottom_layer Metal1 \
    -via_in_pin_top_layer Metal1 -verbose 1
puts "WARP_PIN analysis completed; inspect access statistics and warnings"
write_db "$::env(WARP_PIN_OUT)/pin_access.odb"

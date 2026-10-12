# WARP D-085: copied-script net-order diagnostic; no capacity perturbation.
if {$warp_order_seed > 0} {
    if {[llength [info commands set_global_routing_random]] != 1} {
        error "Pinned OpenROAD lacks required net-order command"
    }
    log_cmd set_global_routing_random -seed $warp_order_seed -capacities_perturbation_percentage 0 -perturbation_amount 1
}

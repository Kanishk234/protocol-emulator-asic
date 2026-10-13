# The SHA-bound source is a completed global screen, not a detailed route.
# It must have no ordinary detailed signal/clock wires. Preserve power/special.
proc tripwire_require_unrouted_screen_source {} {
    set signals 0
    foreach net [[ord::get_db_block] getNets] {
        if {[$net getSigType] in {POWER GROUND}} {continue}
        incr signals
        if {[$net getWire] ne "NULL"} {error "Unexpected detailed wire in global-screen source"}
    }
    if {$signals==0} {error "Empty global-screen source"}
    puts "TRIPWIRE native route reset: cleared 0 ordinary routed wires; source global screen already has none; power/special routing preserved"
}

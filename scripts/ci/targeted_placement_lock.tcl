# Diagnostic boundary: lock every original instance outside a reviewed small set.
proc tripwire_lock_outside {allowed} {
    set saved {}
    foreach inst [[ord::get_db_block] getInsts] {
        set name [$inst getName]
        if {$name in $allowed} {continue}
        set status [$inst getPlacementStatus]
        lappend saved [list $inst $status [$inst getLocation] [$inst getOrient]]
        if {$status in {PLACED FIRM}} {$inst setPlacementStatus LOCKED}
    }
    return $saved
}
proc tripwire_verify_restore_locked {saved} {
    set changed {}
    foreach record $saved {
        lassign $record inst status location orient
        if {[$inst getLocation] ne $location || [$inst getOrient] ne $orient} {
            lappend changed [$inst getName]
        }
        $inst setPlacementStatus $status
    }
    if {[llength $changed]} {error "Unrelated placement changed: $changed"}
}

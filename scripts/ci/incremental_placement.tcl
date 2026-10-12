# Freeze only existing placement while new buffers/diodes are legalized.
# Restore every original status before saving the checkpoint.
proc tripwire_freeze_existing_placement {} {
    set saved {}
    foreach inst [[ord::get_db_block] getInsts] {
        set status [$inst getPlacementStatus]
        if {$status in {PLACED FIRM}} {
            lappend saved [list $inst $status]
            $inst setPlacementStatus FIXED
        }
    }
    return $saved
}
proc tripwire_restore_placement_status {saved} {
    foreach pair $saved {
        lassign $pair inst status
        $inst setPlacementStatus $status
    }
}

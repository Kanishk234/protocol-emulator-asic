# Local prototype only. Exact checkpoint: banked selector screen37669663762.
# Caller must validate source/checkpoint identity, then legalize, route and STA.
proc tripwire_delay_banked_sram_addr8 {} {
    set block [ord::get_db_block]
    set net [$block findNet net9161]
    set driver [$block findInst wire9161]
    set sink [$block findInst u_chip.u_sram.sram]
    if {$net eq "NULL" || $driver eq "NULL" || $sink eq "NULL"} {
        error "Missing audited SRAM address branch"
    }
    if {[[$driver getMaster] getName] ne "sg13cmos5l_buf_2" ||
        [[$sink getMaster] getName] ne "RM_IHPSG13_1P_512x16_c2_bm_bist"} {
        error "Audited address driver or SRAM master changed"
    }
    set expected [lsort {wire9161/X u_chip.u_sram.sram/A_ADDR[8]}]
    set actual {}
    foreach pin [$net getITerms] {
        lappend actual "[[$pin getInst] getName]/[[$pin getMTerm] getName]"
    }
    if {[lsort $actual] ne $expected || [llength [$net getBTerms]]} {
        error "Audited SRAM address connectivity changed: $actual"
    }
    set input [$sink findITerm {A_ADDR[8]}]
    if {$input eq "NULL" || [$input getNet] ne $net} {
        error "Audited SRAM address pin changed"
    }
    set master [[ord::get_db] findMaster sg13cmos5l_buf_1]
    if {$master eq "NULL"} {error "Missing pinned BUF1"}
    if {[$block findInst tripwire_banked_addr8_hold_buf] ne "NULL" ||
        [$block findNet tripwire_banked_addr8_hold_net] ne "NULL"} {
        error "Duplicate SRAM address delay insertion"
    }
    set rails {}
    foreach name {VDD VSS} {
        set rail [[$driver findITerm $name] getNet]
        if {$rail eq "NULL"} {error "Disconnected driver supply"}
        lappend rails $rail
    }
    lassign [$driver getLocation] x y
    set units [$block getDbUnitsPerMicron]
    set buffer [odb::dbInst_create $block $master tripwire_banked_addr8_hold_buf]
    set downstream [odb::dbNet_create $block tripwire_banked_addr8_hold_net]
    [$buffer findITerm A] connect $net
    [$buffer findITerm X] connect $downstream
    $input disconnect
    $input connect $downstream
    foreach name {VDD VSS} rail $rails {[$buffer findITerm $name] connect $rail}
    $buffer setLocation [expr {$x + 2 * $units}] $y
    $buffer setPlacementStatus PLACED
    puts "TRIPWIRE address hold: net9161 -> BUF1 -> SRAM A_ADDR8; legalization and all-corner validation required"
}

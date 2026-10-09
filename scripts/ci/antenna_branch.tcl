# Source must pass exact NL/DEF audit before loading the original strength ODB.
# One identity buffer; preserve all existing antenna cells. Fresh antenna checks
# are mandatory because branch partitioning changes protected wire geometry.
proc tripwire_split_antenna_branch {} {
    set block [ord::get_db_block]
    set net [$block findNet _03831_]
    if {$net eq "NULL"} {error "Missing audited antenna-loaded branch"}
    set expected [lsort {_28807_/Y ANTENNA_1/A ANTENNA_2/A ANTENNA_3/A ANTENNA_4/A ANTENNA_5/A ANTENNA_6/A ANTENNA_7/A _28812_/S1 _28936_/B _28973_/B _29032_/B _29046_/B _29087_/B _44662_/A1 place7617/A}]
    set actual {}
    foreach term [$net getITerms] {
        lappend actual "[[$term getInst] getName]/[[$term getMTerm] getName]"
    }
    if {[lsort $actual] ne $expected || [llength [$net getBTerms]]} {
        error "Wrong audited antenna branch connectivity"
    }
    set driver [$block findInst _28807_]
    if {[[$driver getMaster] getName] ne "sg13cmos5l_nand3_1"} {error "Wrong branch driver"}
    foreach name {ANTENNA_1 ANTENNA_2 ANTENNA_3 ANTENNA_4 ANTENNA_5 ANTENNA_6 ANTENNA_7} {
        if {[[[$block findInst $name] getMaster] getName] ne "sg13cmos5l_antennanp"} {
            error "Wrong audited antenna master"
        }
    }
    set master [[ord::get_db] findMaster sg13cmos5l_buf_4]
    if {$master eq "NULL"} {error "Missing pinned BUF4"}
    if {[$block findInst tripwire_antenna_branch_buf] ne "NULL" ||
        [$block findNet tripwire_antenna_branch_net] ne "NULL"} {error "Repeated branch split"}
    set rails {}
    foreach pin {VDD VSS} {
        set rail [[$driver findITerm $pin] getNet]
        if {$rail eq "NULL"} {error "Disconnected branch power"}
        lappend rails $rail
    }
    set buffer [odb::dbInst_create $block $master tripwire_antenna_branch_buf]
    set downstream [odb::dbNet_create $block tripwire_antenna_branch_net]
    [$buffer findITerm A] connect $net
    [$buffer findITerm X] connect $downstream
    foreach name {ANTENNA_2 ANTENNA_3 ANTENNA_4 ANTENNA_5 _28936_ _28973_ _29032_ _29046_} pin {A A A A B B B B} {
        set term [[$block findInst $name] findITerm $pin]
        $term disconnect
        $term connect $downstream
    }
    foreach pin {VDD VSS} rail $rails {[$buffer findITerm $pin] connect $rail}
    # Initial location near four existing sink/antenna pairs; not a legal-site
    # claim. Caller must DPL, clear inherited wires, reroute and recheck.
    $buffer setOrient R0
    $buffer setLocation 1250400 291060
    $buffer setPlacementStatus PLACED
    puts "TRIPWIRE antenna branch: _03831_ -> BUF4 -> 8 pins; 7 original upstream sinks; all antenna cells retained; fresh physical qualification required"
}

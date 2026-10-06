# Read-only audit of saved OpenDB snapshots; never writes a routed database.
# WARP_ROUTE_SNAPSHOT=SNAPSHOT.odb openroad -exit inspect_route.tcl
read_db $::env(WARP_ROUTE_SNAPSHOT)
set block [ord::get_db_block]
set dbu [$block getDbUnitsPerMicron]
if {[info exists ::env(WARP_AUDIT_ANTENNAS)]} {
    check_antennas -verbose
}
set audit_nets {net53 net143 net1112 net54 net722 net37 net22 net27 net60 net39 net924 u_shell.u_crc._189_ u_shell._0598_ u_shell._0292_ u_shell._0131_}
if {[info exists ::env(WARP_AUDIT_NETS)]} {
    set audit_nets $::env(WARP_AUDIT_NETS)
}
foreach name $audit_nets {
    set net [$block findNet $name]
    if {$net == "NULL"} {
        foreach candidate [$block getNets] {
            if {[string map {\\ ""} [$candidate getName]] eq $name} {
                set net $candidate
                break
            }
        }
    }
    if {$net == "NULL"} {continue}
    foreach term [$net getITerms] {
        set inst [$term getInst]
        set box [$inst getBBox]
        puts [join [list NET $name [$inst getName] [[$inst getMaster] getName] \
            [[$term getMTerm] getName] [[$term getMTerm] getIoType] \
            [expr {[$box xMin]/double($dbu)}] [expr {[$box yMin]/double($dbu)}]] "\t"]
        if {[[$term getMTerm] getIoType] == "OUTPUT"} {
            foreach input [$inst getITerms] {
                if {[[$input getMTerm] getIoType] != "INPUT"} {continue}
                set upstream [$input getNet]
                if {$upstream != "NULL"} {
                    puts [join [list DRIVER_INPUT $name [$inst getName] \
                        [[$input getMTerm] getName] [$upstream getName]] "\t"]
                }
            }
        }
    }
}
foreach inst [$block getInsts] {
    set box [$inst getBBox]
    set x [expr {[$box xMin]/double($dbu)}]
    set y [expr {[$box yMin]/double($dbu)}]
    set master [[$inst getMaster] getName]
    if {[string match *antennan* $master]} {
        set nets {}
        foreach term [$inst getITerms] {
            set net [$term getNet]
            if {$net != "NULL" && [$net getSigType] == "SIGNAL"} {
                lappend nets [$net getName]
            }
        }
        puts [join [list DIODE [$inst getName] $master $x $y $nets] "\t"]
    }
    if {$x < 50 && $y >= 500 && $y < 550} {
        puts [join [list HOTSPOT [$inst getName] $master $x $y \
            [expr {([$box xMax]-[$box xMin])*([$box yMax]-[$box yMin])/double($dbu*$dbu)}]] "\t"]
    }
}

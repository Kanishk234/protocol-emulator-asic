# Read-only command introspection; does not load or modify a design.
foreach command {global_route read_guides read_global_route_segments write_global_route_segments} {
    puts "TRIPWIRE CAPABILITY $command [expr {[llength [info commands $command]] == 1}]"
    if {[llength [info commands $command]] == 1} {
        puts "TRIPWIRE HELP BEGIN $command"
        if {[catch {help $command} reason]} {puts "TRIPWIRE HELP ERROR $reason"}
        puts "TRIPWIRE HELP END $command"
    }
}
puts "TRIPWIRE CAPABILITY probe_complete 1"

# Replay one completed LibreLane GRT stage without modifying its outputs.
# Environment: WARP_GRT_STEP, WARP_GRT_SCRIPTS (pinned scripts directory),
# WARP_GRT_REPORT (new output filename). Native markers retain coordinates.
foreach key {WARP_GRT_STEP WARP_GRT_SCRIPTS WARP_GRT_REPORT} {
    if {![info exists ::env($key)]} { error "Missing $key" }
}
if {[file exists $::env(WARP_GRT_REPORT)]} {
    error "Refusing to overwrite $::env(WARP_GRT_REPORT)"
}
source [file join $::env(WARP_GRT_STEP) _env.tcl]
set ::env(_TCL_ENV_IN) [file join $::env(WARP_GRT_STEP) _env.tcl]
set ::env(SCRIPTS_DIR) $::env(WARP_GRT_SCRIPTS)
set ::env(STEP_DIR) $::env(WARP_GRT_STEP)
set ::env(_SDC_IN) [file rootname $::env(CURRENT_ODB)].sdc
if {![file exists $::env(_SDC_IN)]} { error "Missing input SDC" }
set warp_exclude_file [open $::env(PNR_EXCLUDED_CELL_FILE) r]
set ::env(_PNR_EXCLUDED_CELLS) [read $warp_exclude_file]
close $warp_exclude_file
set warp_corner_index 0
foreach warp_corner $::env(STA_CORNERS) {
    set ::env(_LIB_CORNER_$warp_corner_index) \
        [concat [list $warp_corner] [dict get $::env(LIB) $warp_corner]]
    incr warp_corner_index
}
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
source $::env(SCRIPTS_DIR)/openroad/common/dpl_cell_pad.tcl
set_propagated_clock [all_clocks]
source $::env(SCRIPTS_DIR)/openroad/common/set_routing_layers.tcl
source $::env(SCRIPTS_DIR)/openroad/common/set_layer_adjustments.tcl
set_macro_extension $::env(GRT_MACRO_EXTENSION)
global_route -congestion_iterations $::env(GRT_OVERFLOW_ITERS) \
    -allow_congestion -verbose -congestion_report_file $::env(WARP_GRT_REPORT)
# Deliberately do not write ODB/DEF/guide back to the original stage.

#!/usr/bin/env bash
set -euo pipefail
real_openroad="$(command -v openroad)"
args=("$@")
script_index=$((${#args[@]} - 1))
script_path="${args[$script_index]}"
script_name="$(basename -- "$script_path")"
if [[ "$script_name" == antenna_repair.tcl ]]; then
    printf 'Live incremental experiment must keep antenna repair in the routing process\n' >&2
    exit 1
fi
if [[ "$script_name" == grt.tcl ]]; then
    route_source='source $::env(SCRIPTS_DIR)/openroad/common/grt.tcl'
    reads=0
    routes=0
    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ "$line" == read_current_odb ]]; then ((reads+=1)); fi
        if [[ "$line" == "$route_source" ]]; then ((routes+=1)); fi
    done < "$script_path"
    if [[ "$reads" != 1 || "$routes" != 1 ]]; then
        printf 'Ambiguous incremental script: reads=%s routes=%s\n' "$reads" "$routes" >&2
        exit 1
    fi
    patched="$(mktemp "${RUNNER_TEMP:-/tmp}/tripwire-electrical-incremental.XXXXXX.tcl")"
    while IFS= read -r line || [[ -n "$line" ]]; do
        printf '%s\n' "$line"
        if [[ "$line" == read_current_odb ]]; then
            printf '%s\n' \
                'if {$::env(GRT_ALLOW_CONGESTION)} {error "Incremental repair must disallow congestion"}' \
                'source /usr/local/share/tripwire/electrical_repair.tcl' \
                'source /usr/local/share/tripwire/incremental_placement.tcl' \
                'write_verilog $::env(STEP_DIR)/baseline.nl.v' \
                'set ::env(SAVE_NL) [file rootname $::env(SAVE_ODB)].incremental.nl.v' \
                'set ::env(SAVE_PNL) [file rootname $::env(SAVE_ODB)].incremental.pnl.v' \
                'set tripwire_frozen [tripwire_freeze_existing_placement]'
        fi
        if [[ "$line" == "$route_source" ]]; then
            printf '%s\n' \
                'source $::env(SCRIPTS_DIR)/openroad/common/set_rc.tcl' \
                'estimate_parasitics -global_routing' \
                'write_global_route_segments $::env(STEP_DIR)/baseline.segments' \
                'write_db $::env(STEP_DIR)/rebased.odb' \
                'write_def $::env(STEP_DIR)/rebased.def' \
                'write_verilog $::env(STEP_DIR)/rebased.nl.v' \
                'puts "TRIPWIRE live routing: initial full route initializes capacity"' \
                'global_route -start_incremental' \
                'source /usr/local/share/tripwire/electrical_incremental_targets.tcl' \
                'source $::env(SCRIPTS_DIR)/openroad/common/dpl.tcl' \
                'global_route -end_incremental -verbose' \
                'write_verilog $::env(STEP_DIR)/after_buffers.nl.v' \
                'write_def $::env(STEP_DIR)/after_buffers.def' \
                'write_global_route_segments $::env(STEP_DIR)/after_buffers.segments' \
                'check_antennas -report_file $::env(STEP_DIR)/before_antenna.rpt' \
                'set diode_cell [lindex [split $::env(DIODE_CELL) "/"] 0]' \
                'set antenna_args [list $diode_cell -iterations $::env(GRT_ANTENNA_REPAIR_ITERS) -ratio_margin $::env(GRT_ANTENNA_REPAIR_MARGIN)]' \
                'append_if_flag antenna_args GRT_ANTENNA_REPAIR_JUMPER_ONLY -jumper_only' \
                'append_if_flag antenna_args GRT_ANTENNA_REPAIR_DIODE_ONLY -diode_only' \
                'log_cmd repair_antennas {*}$antenna_args' \
                'global_route -start_incremental' \
                'global_route -end_incremental -verbose' \
                'tripwire_restore_placement_status $tripwire_frozen' \
                'puts "TRIPWIRE live routing: buffer and antenna edits used initialized capacity"'
        fi
    done < "$script_path" > "$patched"
    printf '%s\n' 'write_global_route_segments [file rootname $::env(SAVE_ODB)].segments' >> "$patched"
    args[$script_index]="$patched"
fi
exec "$real_openroad" "${args[@]}"

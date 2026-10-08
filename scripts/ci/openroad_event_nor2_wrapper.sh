#!/usr/bin/env bash
set -euo pipefail
args=("$@")
script_index=$((${#args[@]} - 1))
script_path="${args[$script_index]}"
script_name="$(basename -- "$script_path")"
if [[ "$script_name" == "grt.tcl" || "$script_name" == "antenna_repair.tcl" ]]; then
    read_count=0
    estimate_count=0
    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ "$line" == "read_current_odb" ]]; then ((read_count+=1)); fi
        if [[ "$line" == 'estimate_parasitics -global_routing' ]]; then ((estimate_count+=1)); fi
    done < "$script_path"
    if [[ "$read_count" != "1" ]]; then
        printf 'Expected one checkpoint read, found %s\n' "$read_count" >&2
        exit 1
    fi
    if [[ "$script_name" == "antenna_repair.tcl" && "$estimate_count" != "1" ]]; then
        printf 'Expected one antenna routing audit insertion point, found %s\n' "$estimate_count" >&2
        exit 1
    fi
    patch_dir="$(mktemp -d "${RUNNER_TEMP:-/tmp}/tripwire-event-nor2.XXXXXX")"
    patched_tcl="$patch_dir/$script_name"
    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ "$script_name" == "antenna_repair.tcl" && "$line" == 'estimate_parasitics -global_routing' ]]; then
            printf '%s\n' \
                'if {$::env(GRT_ALLOW_CONGESTION)} {error "Antenna repair must disallow congestion"}' \
                'puts "TRIPWIRE antenna overflow audit: incremental repair completed with congestion disallowed"'
        fi
        printf '%s\n' "$line"
        if [[ "$line" == "read_current_odb" ]]; then
            if [[ "$script_name" == "antenna_repair.tcl" ]]; then
                printf '%s\n' 'if {$::env(GRT_ALLOW_CONGESTION)} {error "Antenna repair must disallow congestion"}'
            fi
            if [[ "$script_name" == "grt.tcl" ]]; then
            printf '%s\n' \
                'write_verilog [file rootname $::env(SAVE_ODB)].baseline.nl.v' \
                'if {[file exists /usr/local/share/tripwire/drop_driver_size.tcl]} {' \
                'source /usr/local/share/tripwire/drop_driver_size.tcl' \
                'tripwire_size_drop_driver driver' \
                '} elseif {[file exists /usr/local/share/tripwire/drop_leaf_hold.tcl]} {' \
                'source /usr/local/share/tripwire/drop_leaf_hold.tcl' \
                'tripwire_delay_drop_leaves' \
                '} elseif {[file exists /usr/local/share/tripwire/drop_event_size.tcl]} {' \
                'source /usr/local/share/tripwire/drop_event_size.tcl' \
                'tripwire_size_drop_cell nor2' \
                '} else {' \
                'source /usr/local/share/tripwire/event_nor2_size.tcl' \
                'tripwire_size_event_nor2' \
                '}' \
                'source $::env(SCRIPTS_DIR)/openroad/common/dpl.tcl'
            fi
            printf '%s\n' \
                'set ::env(SAVE_NL) [file rootname $::env(SAVE_ODB)].eco.nl.v' \
                'set ::env(SAVE_PNL) [file rootname $::env(SAVE_ODB)].eco.pnl.v'
        fi
    done < "$script_path" > "$patched_tcl"
    args[$script_index]="$patched_tcl"
fi
exec "$(dirname -- "${BASH_SOURCE[0]}")/tripwire-openroad-hotspot" "${args[@]}"

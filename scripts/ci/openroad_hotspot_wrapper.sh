#!/usr/bin/env bash
set -euo pipefail
real_openroad="$(command -v openroad)"
args=("$@")
script_index=$((${#args[@]} - 1))
script_path="${args[$script_index]}"
if [[ "$(basename -- "$script_path")" =~ ^(grt|rsz_timing_postgrt|antenna_repair|drt)\.tcl$ ]]; then
    patched_tcl="$(mktemp "${RUNNER_TEMP:-/tmp}/tripwire-hotspot.XXXXXX.tcl")"
    cat > "$patched_tcl" <<'TCL'
if {![llength [info commands ::set_global_routing_region_adjustment]]} {
    error "Pinned OpenROAD lacks region adjustment"
}
proc ::tripwire_reserve_hotspot {} {
    puts "TRIPWIRE hotspot screen: Metal2 region {500 280 700 380}, adjustment 0.30"
    set_global_routing_region_adjustment {500 280 700 380} -layer Metal2 -adjustment 0.30
}
rename ::global_route ::tripwire_global_route_original
proc ::global_route {args} {
    tripwire_reserve_hotspot
    uplevel #0 [list ::tripwire_global_route_original {*}$args]
}
if {[llength [info commands ::repair_antennas]]} {
    rename ::repair_antennas ::tripwire_repair_antennas_original
    proc ::repair_antennas {args} {
        tripwire_reserve_hotspot
        uplevel #0 [list ::tripwire_repair_antennas_original {*}$args]
    }
}
TCL
    if [[ "$(basename -- "$script_path")" == "rsz_timing_postgrt.tcl" && "${TRIPWIRE_BRANCH_REPAIR:-0}" == "1" ]]; then
        read_count=0
        while IFS= read -r line || [[ -n "$line" ]]; do
            if [[ "$line" == "read_current_odb" ]]; then
                ((read_count+=1))
            fi
        done < "$script_path"
        if [[ "$read_count" != "1" ]]; then
            printf 'Expected one checkpoint read, found %s\n' "$read_count" >&2
            exit 1
        fi
        while IFS= read -r line || [[ -n "$line" ]]; do
            printf '%s\n' "$line"
            if [[ "$line" == "read_current_odb" ]]; then
                printf '%s\n' \
                    'source /usr/local/share/tripwire/critical_branch.tcl' \
                    'tripwire_split_critical_branch' \
                    'source $::env(SCRIPTS_DIR)/openroad/common/dpl.tcl'
            fi
        done < "$script_path" >> "$patched_tcl"
    else
        printf 'source [list {%s}]\n' "$script_path" >> "$patched_tcl"
    fi
    args[$script_index]="$patched_tcl"
fi
exec "$real_openroad" "${args[@]}"

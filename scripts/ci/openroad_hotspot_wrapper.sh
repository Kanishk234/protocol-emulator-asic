#!/usr/bin/env bash
set -euo pipefail
real_openroad="$(command -v openroad)"
args=("$@")
script_index=$((${#args[@]} - 1))
script_path="${args[$script_index]}"
if [[ "$(basename -- "$script_path")" =~ ^(grt|rsz_timing_postgrt|antenna_repair)\.tcl$ ]]; then
    patched_tcl="$(mktemp "${RUNNER_TEMP:-/tmp}/tripwire-hotspot.XXXXXX.tcl")"
    cat > "$patched_tcl" <<'TCL'
if {![llength [info commands ::set_global_routing_region_adjustment]]} {
    error "Pinned OpenROAD lacks region adjustment"
}
rename ::global_route ::tripwire_global_route_original
proc ::global_route {args} {
    puts "TRIPWIRE hotspot screen: Metal2 region {500 280 700 380}, adjustment 0.30"
    set_global_routing_region_adjustment {500 280 700 380} -layer Metal2 -adjustment 0.30
    uplevel #0 [list ::tripwire_global_route_original {*}$args]
}
TCL
    printf 'source [list {%s}]\n' "$script_path" >> "$patched_tcl"
    args[$script_index]="$patched_tcl"
fi
exec "$real_openroad" "${args[@]}"

#!/usr/bin/env bash
set -euo pipefail

# LibreLane calls this wrapper instead of OpenROAD. For the GlobalRouting
# script only, shadow the global_route Tcl command so it also writes the
# requested bin-level congestion report. All original OpenROAD arguments and
# routing settings remain unchanged.
real_openroad="$(command -v openroad)"
args=("$@")
script_index=$((${#args[@]} - 1))
script_path="${args[$script_index]}"

if [[ "$(basename -- "$script_path")" == "grt.tcl" ]]; then
    : "${TRIPWIRE_GRT_REPORT:?TRIPWIRE_GRT_REPORT must name the report output}"
    patched_tcl="$(mktemp "${RUNNER_TEMP:-/tmp}/tripwire-grt.XXXXXX.tcl")"
    {
        printf 'set ::tripwire_grt_report [list {%s}]\n' "$TRIPWIRE_GRT_REPORT"
        cat <<'TCL'
if {![llength [info commands ::global_route]]} {
    error "OpenROAD global_route command is unavailable"
}
rename ::global_route ::tripwire_global_route_original
proc ::global_route {args} {
    if {[lsearch -exact $args -congestion_report_file] < 0} {
        lappend args -congestion_report_file $::tripwire_grt_report
    }
    uplevel #0 [list ::tripwire_global_route_original {*}$args]
}
TCL
        printf 'source [list {%s}]\n' "$script_path"
    } >"$patched_tcl"
    args[$script_index]="$patched_tcl"
fi

exec "$real_openroad" "${args[@]}"

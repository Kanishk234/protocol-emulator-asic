#!/usr/bin/env bash
set -euo pipefail
real_openroad="$(command -v openroad)"
args=("$@")
script_index=$((${#args[@]} - 1))
script_path="${args[$script_index]}"
if [[ "$(basename -- "$script_path")" == "grt.tcl" ]]; then
    route_source='source $::env(SCRIPTS_DIR)/openroad/common/grt.tcl'
    route_count=0
    read_count=0
    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ "$line" == "$route_source" ]]; then ((route_count+=1)); fi
        if [[ "$line" == "read_current_odb" ]]; then ((read_count+=1)); fi
    done < "$script_path"
    if [[ "$route_count" != 1 || "$read_count" != 1 ]]; then
        printf 'Ambiguous pinned routing script: read=%s route=%s\n' "$read_count" "$route_count" >&2
        exit 1
    fi
    patched="$(mktemp "${RUNNER_TEMP:-/tmp}/tripwire-route-restore.XXXXXX.tcl")"
    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ "$line" == "$route_source" ]]; then
            printf '%s\n' \
                'source /usr/local/share/tripwire/route_restore_targets.tcl' \
                'source $::env(SCRIPTS_DIR)/openroad/common/set_routing_layers.tcl' \
                'source $::env(SCRIPTS_DIR)/openroad/common/set_layer_adjustments.tcl' \
                'set_macro_extension $::env(GRT_MACRO_EXTENSION)' \
                'read_global_route_segments $tripwire_segments' \
                'write_global_route_segments $::env(STEP_DIR)/restored.segments' \
                'global_route -start_incremental' \
                'global_route -end_incremental -verbose' \
                'write_global_route_segments $::env(STEP_DIR)/noop.segments' \
                'puts "TRIPWIRE route restoration: no design edits; incremental routing only"'
        else
            printf '%s\n' "$line"
        fi
        if [[ "$line" == "read_current_odb" ]]; then
            printf '%s\n' \
                'write_verilog $::env(STEP_DIR)/baseline.nl.v' \
                'set ::env(SAVE_NL) $::env(STEP_DIR)/restored.nl.v' \
                'set ::env(SAVE_PNL) $::env(STEP_DIR)/restored.pnl.v'
        fi
    done < "$script_path" > "$patched"
    args[$script_index]="$patched"
fi
exec "$real_openroad" "${args[@]}"

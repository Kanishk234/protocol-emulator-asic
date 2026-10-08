#!/usr/bin/env bash
set -euo pipefail
args=("$@")
script_index=$((${#args[@]} - 1))
script_path="${args[$script_index]}"
if [[ "$(basename -- "$script_path")" == "grt.tcl" ]]; then
    read_count=0
    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ "$line" == "read_current_odb" ]]; then ((read_count+=1)); fi
    done < "$script_path"
    if [[ "$read_count" != "1" ]]; then
        printf 'Expected one checkpoint read, found %s\n' "$read_count" >&2
        exit 1
    fi
    patch_dir="$(mktemp -d "${RUNNER_TEMP:-/tmp}/tripwire-event-nor2.XXXXXX")"
    patched_tcl="$patch_dir/grt.tcl"
    while IFS= read -r line || [[ -n "$line" ]]; do
        printf '%s\n' "$line"
        if [[ "$line" == "read_current_odb" ]]; then
            printf '%s\n' \
                'source /usr/local/share/tripwire/event_nor2_size.tcl' \
                'tripwire_size_event_nor2' \
                'source $::env(SCRIPTS_DIR)/openroad/common/dpl.tcl' \
                'set ::env(SAVE_NL) [file rootname $::env(SAVE_ODB)].eco.nl.v' \
                'set ::env(SAVE_PNL) [file rootname $::env(SAVE_ODB)].eco.pnl.v'
        fi
    done < "$script_path" > "$patched_tcl"
    args[$script_index]="$patched_tcl"
fi
exec "$(dirname -- "${BASH_SOURCE[0]}")/tripwire-openroad-hotspot" "${args[@]}"

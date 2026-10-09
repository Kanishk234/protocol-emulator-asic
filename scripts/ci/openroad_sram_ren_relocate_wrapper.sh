#!/usr/bin/env bash
set -euo pipefail
real_openroad="$(command -v openroad)"
args=("$@")
script_index=$((${#args[@]} - 1))
script_path="${args[$script_index]}"
script_name="$(basename -- "$script_path")"
if [[ "$script_name" == "grt.tcl" || "$script_name" == "antenna_repair.tcl" ]]; then
    read_count=0
    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ "$line" == "read_current_odb" ]]; then ((read_count+=1)); fi
    done < "$script_path"
    if [[ "$read_count" != "1" ]]; then
        printf 'Expected one native checkpoint read, found %s\n' "$read_count" >&2
        exit 1
    fi
    patched_tcl="$(mktemp "${RUNNER_TEMP:-/tmp}/tripwire-sram-ren-relocate.XXXXXX.tcl")"
    while IFS= read -r line || [[ -n "$line" ]]; do
        printf '%s\n' "$line"
        if [[ "$line" == "read_current_odb" ]]; then
            if [[ "$script_name" == "grt.tcl" ]]; then
            printf '%s\n' \
                'write_verilog [file rootname $::env(SAVE_ODB)].baseline.nl.v' \
                'source /usr/local/share/tripwire/native_hold100_size.tcl' \
                'source /usr/local/share/tripwire/sram_ren_relocate.tcl' \
                'tripwire_relocate_sram_ren' \
                'source $::env(SCRIPTS_DIR)/openroad/common/dpl.tcl' \
                'tripwire_verify_sram_ren' \
                'tripwire_clear_native_signal_routes'
            else
                printf '%s\n' 'if {$::env(GRT_ALLOW_CONGESTION)} {error "Native antenna repair must disallow congestion"}'
            fi
            printf '%s\n' \
                'set ::env(SAVE_NL) [file rootname $::env(SAVE_ODB)].eco.nl.v' \
                'set ::env(SAVE_PNL) [file rootname $::env(SAVE_ODB)].eco.pnl.v'
        fi
    done < "$script_path" > "$patched_tcl"
    args[$script_index]="$patched_tcl"
fi
exec "$real_openroad" "${args[@]}"

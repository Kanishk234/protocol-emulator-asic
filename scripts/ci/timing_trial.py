#!/usr/bin/env python3
"""Apply one named RTL prototype to the exact frozen R4 candidate."""
import os
from pathlib import Path
import subprocess

CANDIDATE = "3393eea9a58c5cad9077cc360a8515d0e5ec8284"
PATCHES = {
    "bs-event-rx-timer": ("bs_event_rx_timer.patch", ("src/trw_pin_bs.v", "src/trw_pin_rx.v")),
    "bs-event-drop-qual": ("bs_event_drop_qual.patch", ("src/trw_chan_port.v", "src/trw_pin_bs.v")),
    "drop-counter": ("drop_counter.patch", "src/trw_chan_port.v"),
    "drop-qual": ("drop_qual.patch", "src/trw_chan_port.v"),
    "bs-resync": ("bs_resync.patch", "src/trw_pin_bs.v"),
    "bs-csa": ("bs_csa.patch", "src/trw_pin_bs.v"),
    "bs-load-flat": ("bs_load_flat.patch", "src/trw_pin_bs.v"),
    "bs-event-late": ("bs_event_late.patch", "src/trw_pin_bs.v"),
    "bs-sample-predicate": ("bs_sample_predicate.patch", "src/trw_pin_bs.v"),
    "bs-resync-event": ("bs_resync_event.patch", "src/trw_pin_bs.v"),
    "bs-resync-load": ("bs_resync_load.patch", "src/trw_pin_bs.v"),
}


def apply_trial(variant, helpers=Path("workflow-src")):
    if variant not in {*PATCHES, "timing-placement", "setup-margin"}:
        raise ValueError("Unknown independent timing trial")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "diff", "--name-only", "HEAD"], text=True).strip()
    if head != CANDIDATE or dirty:
        raise ValueError("Trial requires clean exact frozen hardware")
    expected = set()
    if variant in PATCHES:
        patch, sources = PATCHES[variant]
        expected = {sources} if isinstance(sources, str) else set(sources)
        subprocess.run(["git", "apply", str(helpers / "spikes/r4_floorplan" / patch)], check=True)
    changed = subprocess.check_output(["git", "diff", "--name-only", "HEAD"], text=True).strip()
    if set(changed.splitlines()) != expected:
        raise ValueError("Trial changed unexpected files")


if __name__ == "__main__":
    apply_trial(os.environ["VARIANT"])

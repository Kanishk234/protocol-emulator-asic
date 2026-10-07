# Shared-RX extracted regression and baseline recovery

Manual extraction [37659134964](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37659134964) completes as a diagnostic, but the candidate fails slow setup at -1.427891 ns. Fast hold is +0.059525 ns; slow/typ hold is +0.331955/+0.168051 ns. Fast/typ setup WS is zero. Route37642988571 has final zero DRT violations. None of this is official GDS closure.

The original event-late +125 ps result37581139249 remains the stronger measured baseline: slow setup -0.179789 ns and fast hold +0.037290 ns. Its two reported failures end at U3 RX timer bits23/22, through U0 PIN_A live configuration and pin feedback. Its routed protocol suite37581139271 passes22/22.

## Path audit

Artifact11500243842 was downloaded and its slow max report and final netlist independently cross-referenced. Among the 1000 reported paths, 40 entries violate setup: 39 end at dropped-counter bits and one at fabric channel2 last_seq. All begin at U0 configuration word4 bit11, a PERIOD bit. Worst endpoint is dropped[22] (-1.427891 ns). The original two RX endpoints are not among these reported failures; this is not proof that their slack improved in a matched endpoint comparison.

The worst data path contains no named hold/delay cell. Its largest individual cell arcs include NOR2B 0.955877 ns, NAND2 0.835914 ns and NAND4 0.832639 ns. The repair log records1080 inserted hold buffers versus180 in the original125ps repair. These observations identify a different critical cone and changed physical optimization; they do not establish hold insertion as the sole cause. A larger arithmetic implementation can alter mapping, repair and placement across the full chip.

Raw evidence remains local: /tmp/shared-rx-extracted-37659134964.zip, /tmp/shared-rx-max.rpt and /tmp/shared-rx-failing-endpoints.json. No raw logs are committed.

## Smaller follow-up

Retain original RX and event-late bit timing. Prepare the already equivalent banked pin-selector on that baseline, changing only trw_pin_io and trw_pin_bs. No extra state, cached configuration or protocol-specific hardware. The IO-only probe maps1.5% smaller and improves pad-to-selection by69.066 ps, while C_ACTIVE-to-selection worsens121.828 ps. This cannot promise recovery of179.789 ps full-chip slack; physical verification must inspect all setup and hold endpoints.

Combined patch: spikes/r4_floorplan/bs_event_pin_banked.patch. Local verification directory: /tmp/event-banked-baseline-verify-20261007. Physical follow-up not launched in this audit. Shared-RX official integration remains provisional and is not eligible for promotion with this setup result.

Local follow-up verification passes60/60 pin tests,5/5 chip tests and2048-clock model/RTL lockstep, zero failures/errors/skips. Source audit confirms only trw_pin_bs.v and trw_pin_io.v differ from frozen hardware; RX is byte-identical. The first pin invocation omitted the frozen cached-carrier harness option and reproduced known BUG73 (58/60); a second invocation reused the old compiled image. A fresh build with CACHED_CARRIER=1 passes all60; superseded fixture runs are not claimed as RTL failures. No physical timing improvement is claimed.

## Screen preparation and final shared-RX functional result

Shared-RX routed GL37659138336 passes22/22, zero failures/errors/skips, independently parsed artifact11501802812. Functional success does not qualify the -1.427891 ns timing result.

Added manual screen choice bs-event-pin-banked and exact BS/IO source guard; RX mutation is rejected. Source hashes now include IO. Combined patch applies cleanly to frozen source and reproduces all three tested BS/IO/RX files byte-for-byte. Helper tests pass159/159 (timing_trial, route_source, placement_route). Screen remains unlaunched until helpers/workflow/patch are published. Downstream route support is deliberately not enabled before screen evidence.

After publishing these changes, dispatch the matched screen with:

```sh
gh workflow run gds-drop-counter-screen.yaml --repo Kanishk234/protocol-emulator-asic --ref main -f experiment=bs-event-pin-banked -f comparison_baseline=bs-event-late
```

Judge the matched results by all-corner setup/hold, overflow, instance area and residual endpoint paths; a GRT-only zero setup WNS does not establish extracted closure.

Corrected screen37669663762 is active on cf78cde after BUG74 runner registration fix. Prepared local routed follow-up support with required IO fingerprint, unchanged successful-main provenance and125ps-only optional headroom repair (fresh fast margin at least50ps; all-corner setup/hold and physical gates unchanged).196 helper tests pass, including a workflow-catalog test that checks every screen input against both patch mapping and runner. This preparation does not authorize routing a failing source; inspect screen evidence before publication/dispatch.

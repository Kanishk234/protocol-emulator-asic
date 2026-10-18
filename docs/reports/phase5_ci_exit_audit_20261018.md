# Phase-five CI applicability audit, October 18

Current audited source: a81eac9b3525ff149a683bc959069f25a62da0df. GitHub run metadata was queried directly. Phase-five exit remains open while the current fabric suite and routing build/collector are active; do not equate a diagnostic collector's success with native routing acceptance.

| Check | Actual evidence | Scope/status |
|---|---|---|
| lint |39143346149|Current source SUCCESS|
| docs |39143346067|Current source SUCCESS|
| test |39143345904|Current source SUCCESS; ordinary chip-test scope|
| unit |39143345967|Current source SUCCESS|
| autonomous supervisor checks |39143345890|Current source SUCCESS; finite test supervision, no background AI|
| formal |39143521760|Current source SUCCESS, all f1_isolation/f2_loader/f3_fifo/f4_prims jobs; no broader formal claim|
| fabric |39143345914|Current source in progress at inspection|
| gds/precheck/gl_test |37659595229 at927b225d72c53ba60a606de75c7e99359cc0202b|SUCCESS; git diff against current source is empty for src, info.yaml, arch, macro, test, gds workflow and scripts/gl_local.sh. Carried physical evidence is frozen G1, never compact routing acceptance.|
| template fpga |39143524179|Expected synthesis failure: warp_g1 has no iCE40 implementation. Explicitly excluded from phase gates by accepted D020; no new exemption. Optional phase7 prototype requires generated fabric RTL and a suitable FPGA.|
| nightly |D095 and VERIFICATION current-status pointer|No efpga-only schedule is configured while default main is TRIPWIRE. Existing explicit bounded campaigns carry the named checks; do not advertise an active cron.|
| router build / controlled pair collector |39143345968 /39143364213|Current source active; actual native candidate outcome pending, no physical acceptance.|

The coordinator initially dispatched the template FPGA refresh without noticing D020. The run consumed less than a minute and reproduced the known unsupported-macro failure. Its downloaded 01-synth.log states: Module warp_g1 referenced in tt_um_warp/u_fabric is not part of the design. No template job or hardware source was changed to hide this result. The prior placeholder FPGA success is not evidence for G1.

Experimental collectors can deliberately retain native failures and rejected hypotheses. Their green collection status does not make a rejected physical result acceptable. Preserve original133, best121 and rejected132 separately. No phase checkbox is ticked by this interim audit.

Run links use https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/ followed by the listed ID. Existing phase5 content review and plain-language summary remain the evidence for their separate completed gates.

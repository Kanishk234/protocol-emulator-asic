# Stock baseline: post-CTS repair timeout

Run [39996448720](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39996448720), main1a590d57bc92b887f73662584ec41e89a4323671, failed the145minute stock-screen step. Source/macro hashes, official TT configuration, synthesis, placement and CTS passed. This is not a completed screening pass, routing result or extracted timing measurement.

## Confirmed failure

Post-CTS repair starts17:41:55UTC. It invokes stock repair_timing -setup -setup_margin0.05. It reports2074endpoints and still reports2074at iteration4054near20:02. GitHub stops the step20:02:28. Setup repair never completes; neither hold repair nor global routing is demonstrated. Increasing the timeout is not justified by the observed lack of progress.

The repeated worst endpoint49332/D is a real positive-level-sensitive configuration latch in unit3. The last completed max.rpt samples1000paths with zero reported slack and actual latch time borrowing. This strongly implicates the additional50ps setup repair target; causality still needs a matched setting-only run. Zero reported latch setup slack is not positive setup reserve or full-design closure.

## Fresh completed evidence only

Last completed stage36-openroad-stamidpnr-1 fresh or_metrics_out.json reports only the typical corner:

| Metric | Value |
|---|---:|
| Setup worst slack |0ns|
| Hold worst slack |-0.577002ns|
| Slew violations |0|
| Capacitance violations |0|
| Fanout violations |169|

The worst hold path is a flop-to-SRAM A_DIN[6] path. These are pre-repair, placement-parasitic results, not final failures after hold repair. Fast/slow values in cumulative state_out.json are inherited from earlier stages; do not report them as fresh post-CTS measurements. Fresh all-corner measurements remain mandatory before any routing qualification.

## Matched diagnostic follow-up

Change only the proposed diagnostic project setting PL_RESIZER_SETUP_SLACK_MARGIN from implicit0.05to explicit0. Keep20ns, stock0.25ns clock uncertainty, all sources/macros/density, native scripts/order, image, checker settings and hold repair target unchanged. Do not disable setup analysis or allow negative setup slack. The standard setting is consumed by unchanged stock rsz_timing_postcts.tcl for both setup repair and hold's setup-protection margin. [OpenROAD documentation](https://openroad.readthedocs.io/en/latest/main/src/rsz/README.html#repair-timing) identifies setup_margin as additional slack margin.

This changes an optimizer target, not the acceptance requirement: setup must be nonnegative, fast hold must meet50ps, and all real electrical/antenna/physical gates remain. The project setting is diagnostic only; adopting it in main src/config.json is outside the current AGENTS whitelist and needs explicit review/owner authorization. No main hardware/config or official workflow changed.

Actual unchanged TT tools accept the new generated project config. Single-key JSON comparison confirms the only physical policy delta. Workflow shell/embedded Python syntax and unchanged official-workflow hash pass. No custom image, injected Tcl, physical ECO or flow substitution is used. Stop before DRT. After it completes, inspect fresh corners, hold, electrical and antenna evidence before choosing the next design change or qualifying a route.

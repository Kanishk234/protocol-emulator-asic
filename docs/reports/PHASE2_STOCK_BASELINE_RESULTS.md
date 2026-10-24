# Completed stock-flow baseline and remaining failures

Run [40042584523](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40042584523), head04e9560b6a71f5ad2a750d8153635d2d04049886, completed23:58:37–01:06:53UTC in68m16s. This is successful measurement through stock Classic before DRT, not timing/electrical qualification. Exact full2/4/U0-full/SRAM hardware,20ns,stock0.25ns uncertainty, unchanged image/scripts/checkers and official workflow.

## Actual saved evidence

Fresh stage43or_metrics_out.json reports the typical corner only:

| Metric | Value |
|---|---:|
| Setup WS |0ns|
| Hold WS |+0.246254ns|
| Slew violations |5|
| Capacitance violations |1|
| Fanout violations |180|

Stage39global routing reports3738total overflow: Metal2=19,Metal3=3657,Metal4=62, with30%layer adjustment. This precedes antenna repair; do not call it a final post-antenna congestion audit. Stage42nested fresh antenna check reports0nets/0pins after102diodes were inserted. Cumulative metrics are not substituted for fresh corner reports. There is no extracted/DRT result, and no new fast/slow result from this stock screen.

Of the180fanout violating report rows,169are clock buffers and11signal drivers. Clock-leaf loads reach17against limit8. Remaining signal failures include fanout2330,fanout2427,fanout2053,fanout2425 and seven smaller violations. The five slew rows are driven by30381/Y, with worst slew3.519276ns vs2.507400ns limit; SRAM A_DOUT[15] capacitance is0.071501pF vs0.064pF. Actual errors remain and DRT stays blocked.

## Next matched physical control

Set the documented stock project option CTS_SINK_CLUSTERING_SIZE=8. This targets169clock fanout failures without any protocol logic/state/latency change. It is the only physical-setting delta from40042584523. Leave clock spacing none, setup extra margin0, density56, GRT adjustment/default repair policies,20ns and0.25ns uncertainty unchanged. Smaller clusters can add buffers/area or change skew/congestion; measurement is required, not an assumed fix. Main adoption of project settings outside the AGENTS whitelist remains separate owner review.

## Additional read-only measurement

After the stock physical screen, use existing postgrt_timing.screen with the same final checkpoint as both inputs. It executes only stock STAMidPNR, twice at each corner, without extra Tcl, repair, placement or routing. All original state/ODB/DEF/NL/PNL/SDC files are SHA-bound and must remain unchanged. Reports must contain fresh setup/hold/slew/cap/fanout metrics at all3corners, finite values and repeatable results. Output explicitly states no physical repair, DRT or qualification performed.

The existing reader carries a legacy GRT_ADJUSTMENT0.16 config value; STA does not invoke routing or consume that routing policy. This is not a change to the physical run's0.3adjustment. Source physical hashes enforce immutability. No custom image, engine scripts, physical ECO or physical-flow step substitution is introduced.

Checks before publication: actual official TT --create-user-config passes; exact one-setting/source/workflow identities checked; pinned CTS schema accepts the field; pinned STAMidPNR declares no physical output views. Workflow shell/Python syntax passes. Executed read-only guard controls accept a complete repeatable fixture and reject source mutation, missing metrics and nonrepeatability; these are guard tests, not physical timing evidence.

Next results must show the effect on all actual counts and fresh corner timing. Congestion, signal fanout and SRAM electrical repair still need resolution even if clock clustering helps. Do not route because the diagnostic job is green.

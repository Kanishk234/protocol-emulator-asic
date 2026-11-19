# Status merge candidate: unbounded queue and full-unit safety proofs

The D-192 scratch candidate now passes two local unbounded ABC PDR tasks: its source-extracted queue cone and its actual full pin-unit composition with qualified cache parameters. Reachability tasks also pass. The candidate remains outside production `src/`; no physical qualification or whole-chip formal claim is made.

Run with the project venv active and OSS CAD Suite appended to PATH:

```sh
python scripts/formal_status_queue.py
python scripts/formal_status_candidate_integration.py
```

The separate `formal` workflow includes both commands under a step explicitly labeled as scratch-candidate verification. Remote execution is pending. Official Tiny Tapeout workflows, constraints and qualified hardware remain unchanged.

## Independent queue oracle

The queue proof copies the actual patched producer region and status-register update block verbatim into a generated verification module. It reproduces the actual reset/restart/inactive clearing behavior, with hashes binding native input, patch and extracted cone. Upstream frame/status intents, frame payload/tag, readback payload fields, producer free, live/active and restart are arbitrary. There are no protocol traffic, fairness or fixed-configuration assumptions at these abstract boundaries. Initial reset is asserted for one clock and held deasserted afterwards.

The oracle builds a list: old pending status, new readback, new frame-start, new refused status. Frame output has priority. Otherwise a free output removes the first list item. The remaining first item occupies the one pending entry; more remaining items mean overflow. Assertions compare output/load/tag/data, pending validity/data and exact loss indication every clock. The oracle never drives the candidate.

ABC PDR proves this relation unbounded. Depth-12 Z3 witnesses exercise two statuses accepted together, excess loss from three abstract intents, subsequent buffered delivery and frame output with an older pending status. Applying the same oracle to the original source fails with an actual counterexample. Three semantic mutations of the candidate also fail with witnesses: lose the second pending status, suppress overflow, or bypass older pending data. ERROR/UNKNOWN/timeout do not count as rejection evidence. See [queue receipt](phase3_status_queue_formal_result.json).

This is a source-extracted cone proof, not a proof that all upstream engine behavior satisfies the protocol or that every abstract intent combination can occur on the real engine.

## Actual full-unit composition

The integration proof uses the actual patched `trw_pin_unit`, RX, TX, BITSYNC and pin-input modules, FULL=1, FRAC=8, with USE_LEVEL_CACHE/USE_SAMPLE_DELTA/USE_BITSYNC_ACTIVE all1. It inserts verification includes only into ignored copies. The same independent queue oracle observes actual engine wires. The prior retention assertion is updated from the first-status value to the second-status enqueue value when applicable; the independent list oracle checks that this value is correct.

All assertions present in the candidate remain enabled, including its loss-accounting replacement for the original disproven collision-impossibility assertion. Sticky set/clear/reset priority, RX free gating, RX-vs-BITSYNC merge priority, queue retention/payload/order/loss and existing engine invariants pass unbounded PDR. This closes the previously failing status path for the candidate under the stated interface premises; it does not change the historical native FAIL receipt into PASS.

Premises match the earlier native task: initial reset then deassertion; static arbitrary configuration; PERIOD at least one clock, SAMPLEOFS below PERIOD, nonzero IDLE_BITS and documented stuffing/delimiter threshold; monotonic activation, stable pending TX token, and cache inputs consistent with static configuration. The task does not prove the host/configuration blocks establish those premises, all possible reconfiguration sequences, synchronization or physical timing.

The first integration cover run reached six goals but failed one: three simultaneous status intents were not reached within16clocks. That combination remains covered in the abstract queue task. For the actual engine, an additional **assertion**, not an assumption, now proves unbounded that the triple combination cannot occur. All safety assertions remain intact. The final integration run passes both unbounded safety and all six depth-16 cover goals, including the real two-status acceptance and later buffered delivery. See [integration receipt](phase3_status_integration_formal_result.json) for source/property/tool-log identity and exact witness steps.

## Remaining work

The exact patch now passes the complete55-case selected whole-chip regression under Verilator, with0failures/skips in514.67seconds. This includes chip host/routine/rotation tests, the complete L3module, Phase3memory/recovery/ACK/SPI/1-Wire/PS2/UART/recorded-capture scenarios, and TAP/LOOP/IDLE/PERM/SCALE/native-phase checks. `bash scripts/check_status_candidate_chip.sh` reproduces the run; [aggregate receipt](phase3_status_merge_candidate_result.json) binds script/testbench/patch/log/XML and both formal receipts. The initial normal-sandbox attempt was stopped after sigrok failed libusb initialization; the completed run used the required local decoder access and had no decoder skips. This is RTL simulation, not candidate gate-level or silicon evidence.

Next measure mapped area, setup/hold/electrical margins and routing using the unchanged flow. No storage register was added, but the new combinational logic has not been physically qualified. Adopt only after those results justify it and requalify through official GDS. F-CHAN-4 for main and the aggregate Phase 3 formal exit remain unchecked; scheduler, rotation and other formal obligations are separate.

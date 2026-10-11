# Host capture and replay planning

`host.capture` decodes timestamp bytes from the existing UART capture images.
`host.replay` converts them into relative event timing windows for a replay
test specification. Both work with the unchanged baseline interface.

Save only valid capture-channel payload bytes after draining the preceding
stream, and check the capture image's sticky overflow indication. Do not mix
UART bytes, reset-separated sessions or old shell bytes into the file. Supply a
known upper bound between every observed event: the stream cannot establish
that bound itself. Any overflow invalidates a complete-trace interpretation.

```sh
source .venv/bin/activate
PYTHONPATH=tools python -m host.replay trace.json --max-gap-clocks 100 \
  --stamp-bits 6 --stamp-shift 2 --start-event 2 --event-count 8
```

The selected slice starts at observed event 2 and preserves original event
indices. Its first event is clock zero. `earliest_clock` and `latest_clock`
bound later events relative to it. With prescaling, cumulative timestamp phase
uncertainty is at most one quantum minus one clock on either side, rather than
adding that uncertainty for each event. External gap bounds can narrow windows.
The whole input is checked for a coherent quantized clock schedule before
slicing, by propagating reachable clock intervals through successive timestamp
bins. Selection cannot hide a contradictory subsequence, malformed interval or
loss. Multiple wraps over a long trace are supported when each
individual event gap satisfies the supplied unambiguous-wrap bound.

These windows are correlated through the shared counter phase. They are a
bounded replay specification, not independently selectable certified clock
times. The capture contains no event polarity, pin level, payload or absolute
time. A test author must supply the stimulus values and a coherent schedule;
the tool does not drive a board or infer pin-arrival latency. Equal timestamps
can represent distinct events within a quantum. No device throughput or
supported protocol-rate claim follows from a plan.

Validation: `python -m pytest -q tools/host/tests/test_capture.py
tools/host/tests/test_replay.py` in the project venv. Tests use independent
absolute-clock traces across counter phases, wraps and selected origins,
exhaustively enumerated small clock schedules, plus loss/malformed-input and
CLI checks. No local EDA is required.

## Compile and host planning certificate

`host.certificate` combines an existing current-schema compiler `report.json`
with a `board.budget.plan` service model. It audits the report's listed sources
and bitstream, requires the selected architecture YAML to be one of those
hashed inputs, and checks architecture identity, LUT/primitive capacities and
timing-summary consistency. It records exact report, image and architecture
hashes, pin mapping, tools and compiler options. Inputs must remain available
at the paths recorded by the compiler; run it from the compiler's original
working directory when provenance uses relative paths.

For example, save this as `budget.json`:

```json
{"clock_hz":50000000,"sck_hz":1000000,"arrival_bytes_s":1000,
 "direction":"read","blackout_us":0,"overhead_us":0,
 "burst_bytes":1,"queue_bytes":2}
```

```sh
source .venv/bin/activate
PYTHONPATH=tools python -m host.certificate build/example/report.json \
  arch/warp_g1/arch.yaml budget.json > build/example/planning.json
```

The output preserves three separate conclusions: reported resource fit,
whether the requested clock lies within the compiler's nextpnr timing estimate,
and whether host service/queue sizing satisfies the analytical model. Unknown
compiler timing remains unknown; inadequate timing or bandwidth is reported as
such. Inventing more than the baseline shell's two queue entries is rejected.
The declared rate is an input assumption, not a protocol rate inferred from
the user design.

This is a planning artifact, not physical timing or board-rate certification.
Hashes check local consistency, not independent authenticity. The compiler's
explicit-input scope excludes recursive includes and tool binaries. Extracted
full-chip timing, I/O, configuration loading, protocol behavior and measured
host scheduling remain separate evidence. Simultaneous read/write traffic needs
a shared bandwidth guarantee; two individually acceptable budgets are not a
concurrency proof. Run `python -m pytest -q tools/host/tests/test_certificate.py`
for pure Python validation without EDA.

Add `--format text` for a readable operating summary of the same freshly audited
inputs. It lists parameters, pin roles, resource counts, tied/open ports and
tool versions alongside separate model timing and host queue results. Unknown
timing is printed as unknown. The summary explicitly labels physical timing
unverified and board rate unmeasured. Malformed pin roles, parameter values,
tool-version metadata and tied/open port lists are rejected rather than silently
displayed as valid compiler evidence. JSON remains the default artifact format.

Mapped pin names and roles are also checked against the selected architecture's
`pins.csv`, which must be a hashed compiler input. This rejects plausible-looking
but nonexistent pins and reversed direction roles. JSON includes the pin-table
hash and each mapped pin's physical chip label, direction and fabric BEL; the
text summary adds the physical chip label beside each mapped user port. Host
channel and user-reset labels describe shell signals rather than extra external
package pins. Pin-table agreement establishes a documented mapping, not board
wiring verification or electrical compatibility with an external device.

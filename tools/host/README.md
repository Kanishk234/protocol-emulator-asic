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

# C loader transport-failure recovery coverage

Date: 2026-10-13. Scope: baseline host software; no hardware or architecture change.

The existing C loader checks included an ambiguous failure at the first
LOAD_DATA transaction. They did not systematically cover failures at identity,
state polling, sticky-error clearing, LOAD_BEGIN, later chunks, LOAD_END or final
status. In particular, a transport can report failure after the chip has already
accepted LOAD_END. Returning success or retrying an uncertain transaction would
mislead the caller.

Added 36 fault-injection cases to
`tools/board/tests/test_c_host_model.py`: nine transaction boundaries, failure
before or after chip acceptance, for both word-array and WBIT APIs. The actual
C99 driver is compiled with `-Wall -Wextra -Werror -pedantic` and exercised via
ctypes against the existing independent transaction-level shell model.

Each case requires WARP_IO, immediate termination at the failed transaction,
no automatic RUN, and successful explicit full-image reload into LOADED. The
ambiguous LOAD_END case also checks that the chip can be LOADED while the host
correctly reports IO uncertainty. Reload checks the exact appended forwarding
trace; the model retains events from earlier partial loads.

Local validation (project `.venv`):

```
python -m pytest -q tools/board/tests/test_c_host.py tools/board/tests/test_c_host_model.py
81 passed in 1.33s
```

This closes a test-coverage gap; no driver defect was found and no C behavior
changed. The first draft incorrectly treated the model's lifetime forwarding
trace as per-load storage; the final test checks the saved prefix plus the new
image. This local result is not a CI run, SPI timing test, physical-chip result,
or proof of partial-byte-transfer recovery. Existing `unit` CI discovers these
tests automatically on push.

Remaining independent work: inject truncated/partial SPI transfers in a loaded
pin-level cloud test; test transport recovery across a real reset/reselect and
required reload; validate board-backend timing once hardware is available.
Those are distinct from this transaction-level boundary check. Current phase 5
physical/evidence gates remain open, and no checklist box is ticked here.

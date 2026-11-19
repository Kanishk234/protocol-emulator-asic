# Conditional compiler bounds for ACK tokens

`tripc` can now check a closed single-token lane response contract, accounting
for EVAL/EXEC, state updates, register reads in EXEC, flag results and pending
flags. The checker is protocol-independent; the I2C queries are separate data
in `programs/analysis/i2c_memory_response.json`.

For both memory firmware variants at their default address 0x50:

| Query | Explicit domain | Initial flags | Response-token visibility |
|---|---|---|---|
| Address ACK | DATA 0xA0 or 0xA1, L0 state ADDR | All eight f0–f2 combinations | Within 4 clocks |
| Write-data ACK | Every DATA byte 0x00–0xFF, L0 state XFER | f1=1 (write), other flags arbitrary | Within 2 clocks |

These clocks run **from an input token already visible to L0 at an eligible
EVAL to a new DATA-zero response token visible on O0**. They do not start or
end at a chip pin. They are not WNS, analog timing or a full ACK deadline proof.

## Required contract

The lane runs every clock. Its pipeline, routine and pending flags are initially
idle; both output producers are initially free. The specified input token is
held until dequeued, the other input is empty, and no new input tokens or host
writes arrive during the query. Constants are the compiled constants.
Unspecified register values are unknown, never assumed zero. Calls and an
earlier output to a different port require progress contracts that this checker
does not supply, and therefore return unknown.

The address path selects compare at clock 0, waits at clock 1 because f0 is
pending, selects ACK submission at clock 2, and makes its output visible at
clock 4. The payload path needs one action, with output visible at clock 2.
The pending-flag wait is included even when the initial f0 already equals the
comparison's eventual result.

All listed input values and allowed initial flags are checked: 16 address cases
and 1,024 payload cases per program, 2,080 across the two programs. This does
not establish that the full protocol workload always enters with the required
pipeline, queue and arrival conditions; those invariants still need analysis.

## Run it

From the repository root:

```sh
source .venv/bin/activate
PYTHONPATH=tools python -m tripc programs/i2c_target_eeprom_guard.trw \
  --response-queries programs/analysis/i2c_memory_response.json \
  --response-results /tmp/i2c-response-results.json
```

The normal report includes the domain, flag assumptions, expected token,
horizon and required environment. The optional JSON includes every case and
its trace. Any unknown or counterexample query gives exit status 2 and no
numeric bound. A wrong address query is a bad response contract, not evidence
of a chip failure. The supplied address domain must be updated when overriding
ADDR; using the 0x50 contract with ADDR=0x2A correctly fails.

Default compilation and all 22 firmware image dictionaries remain unchanged.
No hardware, model, encoding, macro, physical configuration or official workflow
is changed. The new RTL check is included through the internal lane Makefile,
so our existing unit workflow runs it under both simulators.

## Independent checks

The focused Python suite checks all 2,080 cases against the independent lane
pipeline and actual fabric model, with three assignments to unspecified
registers per case (6,240 runs). Another 10,000 cases compare known ALU results
against the independent operation model. Adversarial cases cover unknown
registers/time, premature dequeue, missing direction assumptions, wrong address,
CALL, an earlier output, exhausted horizon, output tags, register dependencies
and EVAL-set-over-EXEC-clear pending-flag priority. The checker must refuse a
finite bound when its required information or progress contract is missing.

The exact compiled slot words and constants also run through the actual lane
RTL for all 2,080 cases. Icarus and Verilator each match the 4/2-clock results,
with zero failures/skips. The complete Icarus lane suite passes 7/7 after the
runner integration. The complete non-slow Python suite passes 636 tests, and the final focused response suite passes 39. Source, image, query, result-log and XML hashes are in `phase3_ack_token_bound_result.json`; raw full case traces stay outside Git.

This is conditional bounded checking plus finite independent cross-checks,
not a formal proof, whole-program deadlock certificate, or completion of the
separate L6-FUZZ requirement.

## Remaining path to the Phase 3 ACK gate

Establish the entry invariants and bounds on competing arrivals, input
synchronization/RX publication, fabric service, output backpressure and the pin
unit's linked-edge scheduling. Include the guarded variant's multicast/reset
window and compare the resulting full bound to independent pin observations.
The existing pin-level and official-netlist timing evidence is retained, but
the Phase 3 EEPROM/compiler-bound exit checkbox remains unchecked.

The subsequent [conditional linked-edge budget](PHASE3_ACK_EDGE_BUDGET.md)
composes the RX/TX interface bounds and checks actual entry premises in finite
whole-chip workloads. It narrows the remaining gap to general queue/arrival and
guard-window invariants; it does not convert these token contracts into an
unconditional whole-program certificate.

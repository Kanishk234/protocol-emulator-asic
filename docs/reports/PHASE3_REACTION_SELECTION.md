# Compiler reaction analysis: local selection foundation

`tripc` now analyzes which earlier slots can actually be ready together with
each urgent slot. This replaces the previous list of all earlier urgent slots.
Compiled firmware images are unchanged for all 22 shipped programs.

This is a local selection guarantee at one eligible EVAL, **not a clock bound
from a pin event to a response**. No Phase 3 exit checkbox is completed here.

## What is checked

`tools/tripc/reaction.py` reads fields using the generated YAML encodings and
intersects the ISA §4.2 readiness predicates: validity, state, flags and pending
flags, input availability/tag/head-bit tests, output readiness, and CALL's
implicit non-busy condition. CALL ignores encoded DST; head tests are ignored
for non-input operands, as specified. Contradictory predicates cannot compete.

Both ISA §4.3 scheduler modes are covered. Without an issuable routine, an
earlier non-urgent slot can beat an urgent slot. With an issuable routine, only
earlier urgent slots can beat another urgent slot. An OUT blocked on its output
is not an issuable routine step (ISA §5.3).

If no earlier slot can overlap, the urgent slot selects at the next eligible
EVAL **if it is ready**. If a possible competitor remains, delay is unknown.
This does not say that the competitor will repeatedly win or that the program
is globally unbounded. The analysis conservatively includes program states
and input combinations that might be unreachable through the actual fabric.

## Memory workload example

For `i2c_target_eeprom_guard`, address-ACK submission at L0 slot 3 can overlap
only the two delimiter handlers at slots 0 and 1. The address-compare state is
different, so slot 2 cannot compete. Assuming the held I0 head is DATA excludes
both delimiter handlers at that snapshot:

```python
from tripc.reaction import analyze_lane
import tripwire_spec as S

words = [int(w, 16) for w in image['lanes']['L0']['slots']]
selection = analyze_lane(words, {'i0_tag': (3, S.TAGS['DATA'])})
```

The masked equality `(mask, value)` constrains one snapshot; it is not an
arrival-rate assumption or a promise that a later START cannot occur. No
numeric ACK bound follows from this query alone.

Both memory-lane delimiter slots are mutually exclusive on the CTRL head's low
bit and have no earlier co-ready competitor. They can select while RB is set
if their input/output conditions hold. Restoring the prototype's explicit
`rb == 0` condition makes them impossible to select in a busy-routine context;
the tool does not turn their urgency into a readiness guarantee.

## Validation

Twenty-four focused tests cover predicate conflicts, CALL/RB and ignored DST,
pending/output stalls, different input ports/head bits, invalid contexts, an
always-ready competitor and the memory examples. A deterministic 10,000-snapshot
cross-check uses the independent lane model to check readiness, concrete
co-ready witnesses and selection guarantees in both scheduler modes. It checks
more than 60,000 encoded slot predicates, more than 500 witnesses and more than
100 non-vacuous selection guarantees.

This is **not** the Phase 3 L6-FUZZ exit requirement: it does not generate
whole-program deadlock-free certificates or validate graph-level liveness.
It is finite randomized testing, not a formal proof of the scheduler.

All 22 complete compiled image dictionaries compare identically with the
pre-change compiler, not just slot words. Firmware, model, RTL, physical inputs
and official workflows are unchanged. The full non-slow model/compiler suite passes 597 tests. Source, test-log and image hashes are in `phase3_reaction_selection_result.json`.

## Next

For an end-to-end ACK bound, analyze the state/action chain from received
address through compare/flag completion and ACK submission; bound all channel
waits, competing arrivals and pin-unit scheduling under explicit environment
contracts. Include the guarded variant's multicast/reset window. Then match
the compiler bound to independent model/RTL pin observations. Do not substitute
the conditional seven-clock primitive path for that workload proof.

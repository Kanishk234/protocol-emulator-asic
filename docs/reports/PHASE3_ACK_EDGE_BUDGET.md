# Conditional ACK edge budget and workload checks

The compiler now composes the checked 4-clock address / 2-clock write-data
lane response with the documented RX and linked-TX pipeline. This is an opt-in
conditional digital budget on the unchanged qualified hardware. It does not
prove that every possible transaction establishes the required entry conditions.

| Component | Conservative clocks |
|---|---:|
| Final external RX edge to visible input token | 3 |
| Visible input to visible ACK output | 4 address / 2 write data |
| Free linked TX accepts output | 1 |
| Total final RX edge to armed TX | 8 address / 6 write data |
| Following external falling edge to target low drive | 3 |
| Observation reserve | 1 |

The edge budget requires a free RX producer without an event collision, an
initially idle lane pipeline/routine, free outputs, no competing input arrivals,
and an idle, enabled, selected transmitter. Selection must remain active through
the ACK high phase. Configuration and host writes are excluded during the path.
The compiler checks blocking RX/TX connections, output ownership, linked rising
RX / falling TX, length tokens, open drain, idle-high, no preload/carrier, and a
DATA-only output stream. Unchecked routine calls or control-word writers cause
refusal. Response results are bound to the complete compiled-image SHA-256;
results from another image cannot supply the lane bound. Pipeline constants
cannot be overridden through the profile file.

## Declared environment at a 20 ns clock

The profiles use minimum SCL high/low and data setup requirements from
[NXP UM10204, Table 11](https://www.nxp.com/docs/en/user-guide/UM10204.pdf).
High/low minima become 200/235, 30/65 and 13/25 clocks; setup requirements are
rounded upward to 13, 5 and 3 clocks. These declarations assume the actual
operating clock is 20 ns. They are not pad or analog characterization.

| Profile | Arm margin, address / write | Target-enable setup bound | Required setup |
|---|---:|---:|---:|
| Standard-mode | 191 / 193 clocks | 231 clocks | 13 clocks |
| Fast-mode | 21 / 23 clocks | 61 clocks | 5 clocks |
| Fast-mode Plus | 4 / 6 clocks | 21 clocks | 3 clocks |

Arm margin subtracts the arm bound and one observation clock from the minimum
high interval. Target-enable setup subtracts three drive clocks and one
observation clock from the minimum following low interval. This target-enable
metric differs from the existing controller-released SDA setup measurement:
the target may already be driving low before the controller releases SDA.
Previously revalidated controller-released setup bounds of 620/220/340 ns
remain separate and are not replaced by these numbers.

```sh
source .venv/bin/activate
PYTHONPATH=tools python -m tripc programs/i2c_target_eeprom_guard.trw \
  --response-queries programs/analysis/i2c_memory_response.json \
  --linked-budget programs/analysis/i2c_memory_linked_budget.json \
  --response-results /tmp/i2c-linked-response.json
```

Both memory variants conditionally pass. Unsupported settings or insufficient
budgets return exit status 2. Normal firmware compilation is unchanged.

## Independent observations and negative controls

The whole-chip model executes 32 complete workloads: both firmware variants,
four timing profiles and four initial phase offsets. All 1,120 ACK requests
satisfy the observed entry premises and path limits. The model measures RX
publication at 3 clocks, lane response at 4/2 and TX acceptance at 1, giving
8/6 clocks to arm. Assertions inspect queue freedom, pending flags, pipeline
and routine state, transmitter state, selection, producer sequence numbers,
arrivals and response identity; they do not merely check the final ACK bit.

Both Icarus and Verilator execute 350 internal ACK checks each across both
programs and five timing/phase combinations. Observed RX publication is 2
clocks, lane response 4/2 and acceptance 1, giving 7/5 to arm; falling-edge to
drive is 2 clocks. The model snapshots precede a step and RTL snapshots follow
the active clock edge. The conservative 3-clock interface bounds and observation
reserve are retained rather than retuned to the smaller RTL measurements.

A separate port-only test passes 40 ACKs on Verilator and on the exact official
final netlist from run 44189196098. It checks both firmware variants at 1 MHz
with 25- and 13-clock SCL high intervals, readback, wrong-address NACK, open-drain
behavior and required sigrok decoding. Its observed target-enable setup lower
bounds are 22 and 34 clocks. The flattened netlist test makes no internal entry
premise claim and has no SDF annotation. The RTL-only test is deliberately
filtered out of that replay; selected tests have no failures or skips.

During development a synthetic interruption exposed first-assertion credit in
the new target-enable monitor: drive at clock 16, release at 48, reassert at 49,
sample at 50. The initial monitor incorrectly credited the old interval. The
corrected monitor resets its continuous-low timer on every release and freezes
the final interval at the sample edge. The negative control fails on the old
monitor and passes after correction. Twenty-two monitor checks cover entry,
arrival, latency, selection, unstable-high and missing/unexpected-ACK failures.
This was caught before publication and is not evidence of a chip failure or a
change to the previously corrected controller-released SDA oracle.

Final validation: 716 non-slow Python tests pass; the focused compiler budget
and existing response suites pass 65 tests; all 22 compiled firmware images
remain unchanged. Verilator passes both new chip tests, Icarus passes the
selected internal test, and the official netlist passes the selected port test.
Hashes and selected/filtered test distinctions are recorded in
`phase3_ack_edge_budget_result.json`. Only our unit workflow and internal runner
gain test modules. Qualified physical inputs and official workflows are unchanged.

## Remaining gate

Observed premises in finite workloads are not universal queue/arrival
invariants. Establish a service/arrival envelope for the memory lane, competing
delimiter traffic and guarded selection window, then connect that result to
these conditional bounds. The full I2C/compiler-bound exit checkbox stays open.
No new physical signoff, WNS improvement, analog guarantee, formal proof,
exhaustive recovery or silicon claim follows from this work.

Subsequent [memory-service analysis](PHASE3_MEMORY_SERVICE.md) corrects the old
routine-time estimate and establishes a conditional 51-clock store envelope.
It retains the distinction between no-interference service and an environment
arrival proof; the ACK budget's numbers and remaining gate are unchanged.

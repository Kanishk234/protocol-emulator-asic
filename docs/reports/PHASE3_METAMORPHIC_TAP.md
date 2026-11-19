# L4-TAP: an unserviced observer must not delay the active path

This milestone covers only L4-TAP for finite UART, SPI and I2C workloads. It does
not complete the five-relation L4 exit criterion or prove unbounded tap isolation.
Hardware, encodings, physical config and official Tiny Tapeout jobs are unchanged.

The same existing firmware is compiled twice. The candidate adds only a tap from
L0.O1 to L1.I0; lane 1 remains halted and never consumes a token. The baseline has
that port disabled. Configurations are loaded normally before traffic starts;
no live configuration writes are used. Both copies receive identical commands,
peer parameters and host-service schedules. The added port must accumulate drops
with zero takes; a non-exercised or disabled observer cannot pass vacuously.

## Model coverage

Sixteen pairs compare **517,960 clocks** in total, with both chips stepped on
every compared clock:

- UART:115200/460800baud, clean/bad-stop receive streams, plus simultaneous two-byte TX.
- SPI:mode0 controller at periods50/10/6clocks, six-byte transfers and an independent target.
- I2C:periods500/124/50clocks, stretching0/40/107clocks, writes, wrong-address NACK,
  repeated START, three-byte read and final NACK/STOP.

The model has a one-token host queue drained every560clocks. Each clock compares
protocol outputs, resolved inputs, every existing producer's state/free/load
history, every pre-existing consumer's availability/head/sequence/take/filter
state, host queues/delivery schedule and pin status. Each copy must also pass
its independent functional oracle. Tap drops are5–30per pair and takes remain0.

Three negative controls make the otherwise identical added subscriber blocking.
Each produces an active-path mismatch, so a checker accidentally ignoring
producer stalls does not pass. The focused model suite passes19/19in40.51seconds.

The observer's own availability/drop counter and the expected dropped-event IRQ
are deliberately excluded from equality: those change by design. Protocol pads
and the original blocking path remain in scope; this is not a claim that every
host status/IRQ bit remains identical after adding an observer.

## Chip-port verification

Each protocol runs a baseline/tapped pair through the real SPI host interface.
The load sequence has identical addresses, transaction lengths and timing; only
the added port configuration value differs. Lane1 remains halted. The bench
compares full sampled protocol-output/UIO-bus traces and the host-observed token
queue at the same transaction checkpoints. These are cycle-exact pad checks and
transaction-observed host-delivery checks; RTL does not expose internal producer
states to the bench. A host read of the tap's documented drop counter must change
from0to a positive value. Pin status must match.

Selected profiles:UART460800with framing error, SPIperiod10, I2Cperiod124with40clock
stretch. Both RTL simulators pass3/3paired cases with0failures/skips: Verilator
23.39seconds and Icarus90.10seconds. Measured tap drops are6/5/30 respectively.
The full Python suite passes1,164tests in179.16seconds. The focused19checks
also pass the alternate scheduler in27.39seconds. Exact official-netlist replay
also passes3/3with0failures/skips in275.66seconds. Protocol-trace hashes and
host observation checkpoints are identical across all three simulators. Gate replay uses official44189196098's unchanged
netlist, matching PDK and Icarus13, without SDF or fresh physical signoff.

## Remaining L4 work and scaling audit

| Relation | Status after this milestone |
|---|---|
| LOOP | An existing one-lane UART loop test exists; the required two-lane UART/SPI/I2C coverage remains open |
| SCALE | Open; exact origin and treatment of fixed control latency must be stated before claiming global scaling |
| PERM | Open; use legal fabric/pin mappings and account explicitly for any SRAM rotation phase |
| IDLE | Open; add deterministic random idle insertions and compare decoded sequences |
| TAP | Finite model, both RTL simulators and exact official netlist pass |

A model audit sends UART0x55at1Mbaud and500kbaud. Edge clocks from the first model
step are4,54,...454and4,104,...904. Bit intervals double exactly, while the initial
four-clock lane/arm latency stays fixed. Consequently the raw edge coordinates
are not globally doubled. This is not a chip defect: changing a pin period does
not slow the control clock. The audit is evidence for defining the SCALE oracle
carefully, not permission to silently redefine it, normalize arbitrary gaps or
mark SCALE complete. VERIFICATION.md and the phase exit requirement remain
unchanged; this receipt retains both image hashes and the counterexample.

Reproduce after activating the project venv:

```sh
python -m pytest -q -rP tools/kernels/tests/test_metamorphic_tap.py
make -C test_internal/chip COCOTB_TEST_MODULES=test_metamorphic_tap
```

Own unit CI and the internal aggregator include the chip test; pytest/nightly
find the model suite automatically. Evidence is in phase3_metamorphic_tap_result.json;
raw traces/logs stay untracked. No new physical hardening is needed for these
verification-only changes. Phase3remains in progress.

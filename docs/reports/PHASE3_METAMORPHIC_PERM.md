# Strict fast-path permutation checks and the SRAM-phase counterexample

This milestone tests exact raw-cycle equality for finite legal UART, SPI and
I2C-target mappings. It does not establish unrestricted invariance for every
program or close the full L4/Phase3gate. No timing normalization, trace shifting,
production firmware edit or physical change is used by the positive checks.

## Exact fast-path cases

Compile each existing program with identity mapping, then with units only,
lane only, and both mappings:

- Active lane:L0→L1. The other lane stays halted.
- Unit mapping:U0→U2,U1→U3,U2→U0,U3→U1.
- Physical pad assignments stay unchanged; the transmitting unit's pad ownership
  and every channel endpoint are renamed consistently. The compiler checks the
  legal fabric sources and the selected unit's supported configuration.

All chosen modes are supported on the lean units. These are three declared
mappings, not an exhaustive enumeration of all possible lane/unit/pad assignments.
Compiled local slots, registers, K entries and SRAM are identical under renaming,
and each pin role/owner is preserved at its original physical pad.
Baseline and candidate use the same traffic origin and clock schedule; there is
no pre-start phase adjustment in these positive cases.

Eight profiles cover UART115200/460800with receive framing error and two-byte TX;
SPI controller periods50/10/6with six full-duplex bytes; and I2C target periods
500/125/50with writes, ignored wrong addresses and three read bytes. The I2C
peer's ACK/read log and host's five written bytes must match exactly, with an
extra44remaining unsent. The model queues upstream host commands and has a
one-token output queue drained every560clocks. The chip I2C profile is125clocks,
where the real SPI host refills its read bytes; no continuous1MHzhost-refilled
read claim is made from the faster model profile.

The model performs24candidate comparisons over753,633clocks, matching every
sample of protocol outputs, UIO outputs/enables, resolved UIO and ui0, plus the
complete host delivery schedule. Each copy separately passes the established
independent UART/SPI/I2C peer/framing oracle. Three wrong-owner configurations
must fail their functional oracle. Focused Python checks pass12/12in24.66seconds;
11cover fast-path profiles/negatives and one retains the native routine diagnostic.
The alternate scheduler also passes12/12in18.51seconds; the routine diagnostic
explicitly uses the native one-EVAL-per-clock mode rather than claiming arbitrary
scheduler invariance.

## Port-only chip checks

Each protocol runs identity then combined lane/unit mapping through the real
SPI host loader. The loader writes the same number/length of transactions;
only declared mapping values/addresses change. Protocol/UIO/input traces and
host-observed queues at matching transaction checkpoints must be exactly equal.
Pin status must stay clear. UART460800, SPIperiod10 and I2C-target125are the
selected chip profiles.

Verilator passes3/3paired cases with0failures/skips in21.82seconds; Icarus RTL
also passes3/3in84.46seconds. The full Python suite passes1,187tests in183.42seconds.
Exact official-netlist replay also passes3/3with0failures/skips in289.71seconds.
Trace hashes and host observation checkpoints match across all three simulators;
the receipt records source/image/log/XML identities and the explicit exception. Gate replay uses
official44189196098's unchanged artifact, matching PDK and Icarus13, without SDF
or a new physical signoff claim. This is sampled logical equivalence, not equal
analog propagation delay between differently placed units.

## Counterexample kept visible

The native SRAM-backed I2C **controller** is a separate diagnostic, not silently
substituted into the positive target claim. At period124with40clockstretch,
unit-only remapping is exact. Moving its active lane without changing the start
phase preserves host data and sampled delivery checkpoints but changes349sampled clocks; the first raw
trace difference is3542. Its SRAM grant slot depends on physical lane index.
One real idle clock before configuring the moved model matches the relative
grant phase and restores exact trace equality. No recorded samples are shifted
or edited. That observation is model-only and explicitly native; there is no
corresponding RTL/gate routine-phase qualification in this milestone.

The automated diagnostic requires the unaligned waveform to differ and data to
match, as well as the aligned/unit-only cases to be equal. A green diagnostic
means the counterexample was reproduced, not that unrestricted controller PERM
passed. Similarly, the earlier UART SCALE audit has fixed launch latency even
when programmed bit intervals double.

[D-191](../DECISIONS.md) was subsequently explicitly approved by the user and
adopted in VERIFICATION.md/phase wording. The full L4 exit checkbox remains
unchecked; approval is not evidence that SCALE or hardware routine-phase
checks pass. This report's positive cases stand on their strict
raw equality under the existing wording; they do not waive the counterexample or establish the additional phase-matched hardware case.
Only our unit workflow/internal aggregator gain the chip suite; pytest/nightly
discover the model checks. Evidence is phase3_metamorphic_perm_result.json.

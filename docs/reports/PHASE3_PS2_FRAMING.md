# PS/2 framing and unmodified-capture verification

The existing `ps2_host.trw` is unchanged. New checks exercise its start/stop
mask and parity handling independently, including rejection followed by a clean
frame. The historical recorder-only extra clock has been removed from both
model and chip RX captures. Model, Icarus RTL, Verilator and the exact official-netlist replay pass.
The final replay passes all three selected cases in 1,370.34 seconds, with
zero selected failures or skips; twenty unrelated cases are filtered out.

## Independent decoder

The installed decoder consumes a twelfth falling edge before emitting an
eleven-bit device-to-host frame. Official upstream already completes the frame
on its actual final rising edge. The unmodified upstream implementation is
pinned at [71f451443029322d57376214c330b518efd84f88](https://github.com/sigrokproject/libsigrokdecode/tree/71f451443029322d57376214c330b518efd84f88/decoders/ps2)
in `test_internal/vendor/libsigrokdecode_ps2`, retaining headers and COPYING.
Source headers permit GPL-2.0-or-later; the retained GPL-3.0 text supplies the
later-version option used here. It is a verification dependency, not ASIC RTL.

`tools/sigrok_support.py` selects this package for PS/2 subprocesses only and
checks source/license hashes before use. Other protocols keep their existing
decoder environment. Required calls reject a missing/disabled decoder. The
repository vendor audit now checks two pinned verification packages.

On the same isolated eleven-clock capture, stock emits no word and the pinned
decoder emits 0x5A. No sample changes between those invocations. Sixteen fixture
cases check four data patterns, both parity states and both stop values. The
capture hash must remain unchanged, and decoded individual bits must equal
the actual eleven clocked bits.

## Fault coverage and scope

The independent PS/2 source now has explicit start/parity/stop fault controls;
default behavior is unchanged. The wire monitor collects resolved falling-edge
samples in eleven-bit words and checks the actual injected words. A separate
classification oracle checks framing and odd parity to predict DATA versus
full raw ERR tokens. Invalid-start cases are deliberately clock-complete frames,
not arbitrary missing/extra-clock or timeout-resynchronization tests.

The model matrix is six byte patterns, all eight fault combinations, and three
clock rates (10, 12.5 and approximately 16.7 kHz): **144 scenarios / 288 frames**,
each defective frame followed by a clean frame. An eight-frame capture separately
checks both independent decoded bytes and all stop/parity bits. Disabling only
the scratch instance's start/stop mask fails the oracle on two framing flips
that preserve parity; parity-only coverage would miss that regression.

The full non-slow Python regression passes **1,117 tests**: 146 new framing
tests, 16 decoder fixtures and three helper/gating checks are included.

Both RTL simulators pass three selected chip tests: the new sixteen-frame
matrix at the fastest tested clock, the retained six-frame RX/parity case and
the retained four-byte host-to-device case. The new matrix includes seven ERR
words, nine DATA words and eight clean recovery frames; all 176 real clock
falls are checked. Twenty unrelated L3 tests are deliberately filtered out of
these focused runs and remain distinct from selected-test skips.

The pinned decoder is explicitly device-to-host. It validates the new capture's
eight valid-start prefix frames, including their actual bad stop-bit values,
and all six legacy RX frames. After invalid starts a protocol-aware decoder can
resynchronize differently, so the raw-clock oracle and chip ERR checks cover
the full sixteen-frame matrix. No claim is made that sigrok itself validates
stop-bit legality or arbitrary malformed-start recovery. Host-to-device framing
is checked separately against the external peer.

Own unit CI and the internal aggregator include the new test. Official workflow
jobs, RTL, macros, physical configuration, encodings and all 24 firmware images
are unchanged. Receipt `phase3_ps2_framing_result.json` records sources, package
identity, control capture, test logs/XML and gate status. Gate replay uses
official run 44189196098's final netlist and matching PDK with Icarus 13, without
SDF or new physical signoff.

## Combined protocol audit

The retained WS2812 and DShot scenario function ASTs match the qualified source
and their programs compile identically. Their 22-case final-netlist evidence
from run 44123392388 can be retained at the documented finite scope. Qualified
unit run 44189195981 supplies their RTL evidence; the qualified workflow runs
`test_l3` on Icarus and Verilator. The receipt retains that workflow identity
and the current/qualified scenario AST comparisons.

The WS2812 checker matches the classic manufacturer-authored
[Worldsemi WS2812B timing table](https://cdn.sparkfun.com/assets/e/6/1/f/4/WS2812B-LED-datasheet.pdf):
the named pulse windows and reset above 50 us. The old broad SK6812/variant
source comment has been narrowed without changing any emitted word. Actual
voltage/interface and other LED variants need separate qualification.

DShot retains five payload/telemetry pairs at the four named program rates,
with checksum and the existing declared pulse/duty tolerances. The protocol
reference is the [Betaflight DShot documentation](https://betaflight.com/docs/development/API/Dshot).
This is not universal ESC interoperability or exact analog bitrate evidence.
The installed sigrok package has no DShot decoder, so the separate all-L3-sigrok
checkpoint remains open; a project timing checker is not relabelled as sigrok.

The combined functional protocol checkpoint is checked using these retained
results plus the new SPI memory and 1-Wire reports, each within its documented
finite scope. This does not complete the separate independent-decoder gate. The other Phase 3 gates, including decoder/capture expansion, formal,
compiler certificates and FPGA, remain open.

```sh
source .venv/bin/activate
python -m pytest -q tools/kernels/tests/test_ps2_framing.py \
  tools/kernels/tests/test_sigrok_ps2.py tools/kernels/tests/test_sigrok_support.py
make -C test_internal/chip SIM=verilator \
  COCOTB_TEST_MODULES=test_ps2_framing,test_l3 COCOTB_TEST_FILTER=ps2
```

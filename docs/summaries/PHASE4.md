# Phase 4 summary: protocols, showcase, held-out evaluation

**Status:** complete (2026-09-28). The new chip tests passed in `gl_test` 36451108163 and `fabric` 36451328356; `unit`, `lint`, `test`, and `docs` were green on 14e7063. The optional stretch protocols remain unattempted.

## Goal
Show what the frozen chip can do, with bitstreams and tests only (no silicon changes): run the held-out protocols the architecture never saw, give users the software side (compile, load, examples), and test robustness.

## What we did
- **Held-out protocols** (sealed since phase 1, opened after `hw-freeze`): each with an independent reference model written first from its own specification, then the design in hard-primitive and plain-logic forms, RTL tests, compilation onto the frozen chip and onto the plain-LUT baseline, and a chip-level test through the host interface (`docs/reports/heldout_results.md`):
  - **WS2812** fits (32 of 88 logic cells), **1-Wire** fits (77; it does not fit the plain fabric at all), **SWD** fits (44; packets in host software), **CAN 2.0A does not fit** (207).
- **Software side** the organizers asked for (D-032): a demo-board loader (`tools/board/warp.py`), board-side protocol helpers (`tools/board/examples.py`), an SWD host library (`tools/board/swd.py`), `compile --set`, and an end-to-end guide (`docs/EXAMPLES.md`). The board code itself is tested against the chip model.
- **Showcase** (D-036): one chip, never reset, loads six protocols one after another through the host interface and each works against its reference device.
- **Robustness:** a corrupt load over a running design (the chip ends in ERROR, keeps every pin parked, refuses RUN, then recovers with a valid load); UART input edges at random phases of the clock; a mutation campaign (11 planted bugs, all caught locally, `docs/reports/mutation.md`); a co-simulation showing the UART bitstream on the fabric produces the same waveforms as its source RTL.

## What we found
- **The primitives generalized**: every held-out design uses both block types, in ways the design set never did (a pulse-width generator, a 480 µs one-shot, an SWD bit clock, a CAN sample point); they save 17–50 logic cells per protocol and decide whether 1-Wire fits.
- **Capacity is the limit of generality**: CAN's frame parser is about 2.4 × the fabric.
- **Active-low outputs on `uo_out` pins are asserted while the chip is stopped** (BUGS #19): the fix is at the pin map (bidirectional pin + pull-up), and it matters most for CAN (a parked 0 would jam the bus).
- **Timing**: designs must avoid combinational paths through a timer's enable (WS2812 went from 42.5 to 54.3 MHz by tying it high).

## What's left
- Optional stretch protocols (PS/2, JTAG) were deferred; they are outside the phase exit checklist.

## One-line takeaway
The frozen chip runs three of four protocols it was never designed for, loads any of six protocols at run time without a reset, and every planted bug in the campaign was caught.

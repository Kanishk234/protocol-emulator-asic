# Shared-image event lanes (architecture candidate)

This spike measures one candidate for a successor to G1. It is not part of the active chip architecture. G1 remains the baseline.

## Objective

Test whether two independently paced, protocol-neutral event lanes can share a small instruction image and leave packet transforms, CRCs, unusual state machines, and custom parallel logic in an eFPGA fabric. Two memory policies are screened: runtime writable storage and an image held in the fabric's configuration latches. The intended distinction from a standalone PIO block is the composition: lane outputs and captured pin events are available to a reconfigurable fabric, which can monitor or transform traffic while another lane performs timed pin work.

## Interface and state

- Two lanes, each with a parameterized 3- or 4-bit program counter, `busy` and one-cycle `irq` pulse.
- One shared program image of `2**AW` × 24 bits (8 words by default, with 16 words as an area sweep). Both lanes have independent combinational fetch addresses and can execute the same program at different PCs.
- The RAM variant accepts writes only while both lanes are idle (`prog_ready`). The static variant treats the image as outputs of 192 or 384 configuration latches and has no runtime write port.
- Each lane has independent output value, output-enable mask, 8-bit pin sample register, 16-bit delay counter, and 8-bit shift state.
- Both lanes observe the same 8 sampled input pins in this first integration-agnostic model. Their output requests remain separate; pad arbitration and eFPGA wiring are outside this spike.

## Instruction encoding

All instructions are 24 bits: `opcode[23:20]`, `arg0[19:12]`, `arg1[11:4]`, `target[3:0]`. The program has eight words, so control-flow targets use only `target[2:0]`.

| Opcode | Operation | Behavior |
|---:|---|---|
| 0 | NOP | Advance PC by one. |
| 1 | DRIVE | Set selected output bits to `arg1`; add `arg0` bits to the output-enable mask; advance. |
| 2 | RELEASE | Clear `arg0` bits in the output-enable mask; advance. |
| 3 | WAIT_PINS | Stall at this instruction until `(pins_in & arg0) == (arg1 & arg0)`, then advance. |
| 4 | DELAY | Wait for the unsigned 16-bit count `{arg0,arg1}`; advance after that many subsequent lane clocks. A zero count advances on the next lane clock. |
| 5 | SAMPLE | Copy `pins_in` into the lane's sample register; advance. |
| 6 | BRANCH_SAMPLE | If `(sample & arg0) == (arg1 & arg0)`, set PC to `target[2:0]`; otherwise advance. |
| 7 | JUMP | Set PC to `target[2:0]`. |
| 8 | HALT | Clear `busy`, pulse `irq`, and retain output value and enables until a later RELEASE or reset. |
| 9 | SHIFT_OUT | Serialize `arg1` on the pin selected by `arg0[2:0]`; `arg0[3]` selects MSB-first; `target[2:0]` is bit count (0 means 8). Each bit takes one lane clock. |
| 10 | SHIFT_IN | Sample the pin selected by `arg0[2:0]` for the count in `target[2:0]` (0 means 8); `arg0[3]` selects shift order. Publish the final shift-register value in `sample`. |

For `SHIFT_IN`, MSB-first shifts the sampled bit into the low end; LSB-first shifts it into the high end. The sample is the full 8-bit shift-register value, including zero fill; partial transfers are not normalized into a byte. For an image with `AW=3`, instruction address bit 3 must be zero for JUMP/BRANCH_SAMPLE; an invalid target falls through to the next word. With `AW=4`, all four target bits select an instruction address.

Reset is synchronous active-low for control and lane state. It clears lane outputs and status but does not initialize the shared program image. `start` is accepted only for an idle lane and loads its start PC; it does not execute an instruction on that same edge. A running lane executes at most one instruction per clock. Pin waits stall until their predicate completes; delay and shift instructions occupy their stated number of subsequent lane clocks. A branch or jump changes PC on its execution edge. A halted lane produces a one-cycle `irq` pulse.

## What this experiment can establish

The spike can check instruction semantics, lane independence, shared-image programming safety, synthesis structure and rough mapped area. It cannot establish routed area, timing, fabric integration, external pin ownership, bitstream compatibility, or a competition-level advantage. Run `spikes/event_lanes/run.sh` for both testbenches, warning-clean lint and 8-/16-word RAM/static synthesis screens. The static image's mapped latch area is added separately using the SG13G2 `sg13g2_dlhq_1` cell area. The next gate is a compiler-ready configuration mapping and a concurrent lane-plus-fabric workload. Do not test or tune against the previously opened held-out protocols here.

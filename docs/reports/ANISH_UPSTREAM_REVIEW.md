# Architecture checkpoint after upstream updates

Inspected 2026-09-25: `origin/main` at `43282b4`, `origin/efpga` at
`b45a1d8`. These are upstream reports, not physical runs repeated on
`anish_branch`. The histories remain separate.

## Recommendation

Continue evaluating a specialized eFPGA with a fixed shell and no on-chip
CPU. Treat this as a candidate, not a completed capacity decision. A generic
fabric is still the control experiment. Keep TRIPWIRE as the alternative
until an actual mapped and routed protocol workload establishes which
approach fits. Neither branch currently proves an integrated chip fits.

## What changed

- [FABulous reference report](https://github.com/Kanishk234/protocol-emulator-asic/blob/b45a1d8/docs/reports/fab_demo.md):
  FABulous 2.2 works with OSS CAD Suite 2026-06-29. Its newer September
  counterpart has an incompatible synthesis interface. Use the supported
  release, not local replacement technology maps. The two upstream reference
  bitstreams pass separately; our additional experiment exercises A/B/A
  reload in one persistent simulation and reset while enable is low.
- [Capacity report](https://github.com/Kanishk234/protocol-emulator-asic/blob/b45a1d8/docs/reports/capacity.md):
  a 4-by-3 layout is estimated to provide 96 LUT4s, or 88 with one primitive
  tile. Generic synthesis demand is 144/100/164/240 LUT4s for UART, SPI
  controller, I2C controller and I2C target. These demand numbers motivate
  specialization; they do not measure its final savings.
- [Pin-unit RTL report](https://github.com/Kanishk234/protocol-emulator-asic/blob/43282b4/docs/reports/PIN_UNIT_RTL.md):
  TRIPWIRE's lean pin unit is 29,395 square micrometres before layout;
  configuration, host ports and producers add cost. The reported full-chip
  estimate remains around 85% core occupancy. Its timer ablations and
  mutation-tested pin behavior are useful comparison methods. That branch
  also needs area reduction and integration evidence.

## Why the capacity decision is still conditional

The estimated specialized I2C controller consumes about 77 of 88 LUT4s.
That leaves 12.5% spare, below this branch's proposed 20% margin. At 80
LUT4s with two primitive tiles it leaves only 3.75%. Adding 30% glue to an
optimistic subtraction is a sensitivity assumption, not measured mapping.

The upstream area model calculates a primitive tile about 1.07 times the
LUT tile's area but its grid width/height calculations still use LUT-tile
dimensions for every slot. A rectangular placement, edge tiles, shell,
clock/configuration distribution and PDN must establish actual fit. Do not
count the same physical slack both as primitive growth and routing margin.

The I2C target remains outside the proposed capacity. Dropping concurrent
protocols or reducing the register map changes the product requirements;
keep those tradeoffs visible rather than labeling the four-role design set
complete. A register-file primitive deserves an explicit experiment: record
its interface, access latency, ports and use by at least a second workload.

The previously observed 28.57 MHz counter result on this branch came from
the generic nextpnr demonstration timing model and a now-discarded mapping
workaround. It is not a CMOS5L timing result, and it does not validate the
50 MHz chip target.

## Next experiments, in order

1. Close reference-flow correctness with pinned tools: distinct images,
   independent pin-level oracle, reset/enable combinations, wraparound,
   A/B/A reload, wrong-image negative control and bitstream/source hashes.
   **Current blocker:** the [local reload experiment](ANISH_REFERENCE.md)
   passes individual images but stalls while replacing the first image.
   Frame snapshots and a live probe now demonstrate an intermediate LUT
   feedback loop; follow the [reload repair plan](ANISH_RELOAD_PLAN.md)
   before claiming safe runtime reprogramming. Include the repair's cost
   in the existing tight capacity budget.
2. Reuse the upstream protocol semantics and tests as an explicit baseline.
   Fix host buffering, SPI modes, I2C stretching, target register-map size,
   clock and reset behavior before measuring any hardware replacement.
3. Build and map one timer/shift candidate at a time. Resynthesize complete
   protocols with real primitive instances; retain the residual control,
   handshakes, muxes, FF packing and routes in the resource count.
4. Route the 4-by-3 candidate with real primitive dimensions and the shell.
   Report all five declared seeds, routability and timing; require the
   declared headroom on a complete workload. Compare with TRIPWIRE under
   the same buffering, host bandwidth and protocol semantics.
5. Resolve I2C-target storage and competition eligibility before freezing
   the architecture. CPU software convenience alone does not justify adding
   an instruction core and program memory.

The simulator checks logical reconfiguration through the reference loader.
It does not prove safe physical partial configuration, output parking,
metastability behavior, failed-load recovery or gate-level timing. Those
remain shell and physical-verification gates.

# Phase 0 — in progress

The goal is to prove both the ASIC build flow and the FPGA programming flow
work before committing to a custom fabric.

On `anish_branch`, the pinned FABulous reference flow now compiles two
different circuits. Independent simulation checks pass for a 16-bit
counter and an LFSR; deliberately loading the wrong image is detected.
These are reference-fabric results, not measurements of our eventual chip.

Loading the second circuit into the already-running fabric fails. Frame
analysis and a live diagnostic show an intermediate LUT feedback loop.
The failure is preserved as a regression. A reference-only LUT/carry hold
candidate now passes both reload directions, full counter wraparound and
recovery from two interrupted loads. This is a useful repair candidate;
broader path coverage, safe output release and physical cost remain open.
The later [guarded-wrapper experiment](../reports/ANISH_GUARDED_RELOAD.md)
demonstrates parked outputs and reset before pad release, with functional
checks on mapped guard/LUT netlists and initial isolated area measurements.
That full-fabric wrapper still trusts image validity. A separate
[validator/guard experiment](../reports/ANISH_IMAGE_VALIDATOR.md) now passes
41 cases in RTL and on a mapped CMOS5L netlist, checking image format,
completeness and checksum. The later
[validated fabric wrapper](../reports/ANISH_VALIDATED_FABRIC.md) connects it
to the real loader and passes both reload directions and selected bad-load
recovery cases. Reducing management area, covering broader isolation paths
and complete physical validation remain open.
An optional [byte-at-a-time CRC](../reports/ANISH_BYTE_CRC.md) reduces the
matched isolated validator/guard area by 5.88%, with the same rejection
suite passing in RTL and gate-level simulation. This is a block-level
tradeoff, not a demonstrated full-chip area or timing improvement.
The [loader-inclusive measurement](../reports/ANISH_LOADER_COST.md) now maps
the actual loader and its 448 staging bits as well. Both CRC variants pass
mapped control-path tests with counter/LFSR payloads. The 14-row reference
loader dominates this bounded cost; fabric configuration storage, host and
physical implementation remain outside it.
The [word-only loader candidate](../reports/ANISH_WORD_ONLY_LOADER.md) removes
unused serial configuration frontends and now also passes all nine selected
reload/rejection/recovery scenarios on the live reference fabric with byte
CRC. This extends the earlier bounded mapped cost evidence; full-fabric
gate-level checks, arbitrary-image isolation and physical fit remain open.
See the [candidate results](../reports/ANISH_RELOAD_EXPERIMENTS.md), the
[evidence report](../reports/ANISH_REFERENCE.md) and
[repair plan](../reports/ANISH_RELOAD_PLAN.md).

Phase 0 is still open. Reload correctness, organizer questions, recorded CI
results, physical integration and the remaining checklist items must be
resolved before specialization is treated as validated. No phase gate is
closed by this summary. The leading candidate remains a specialized eFPGA
behind a fixed management shell; capacity and physical evidence must decide
whether it is viable.

# Phase 0 — in progress

The goal is to prove both the ASIC build flow and the FPGA programming flow
work before committing to a custom fabric.

On `anish_branch`, the pinned FABulous reference flow now compiles two
different circuits. Independent simulation checks pass for a 16-bit
counter and an LFSR; deliberately loading the wrong image is detected.
These are reference-fabric results, not measurements of our eventual chip.

Loading the second circuit into the already-running fabric fails. Frame
analysis and a live diagnostic show an intermediate LUT feedback loop.
The failure is preserved as a regression, and the next work is to develop
and price a reliable loading/isolation mechanism. See the
[evidence report](../reports/ANISH_REFERENCE.md) and
[repair plan](../reports/ANISH_RELOAD_PLAN.md).

Phase 0 is still open. Reload correctness, organizer questions, recorded CI
results, physical integration and the remaining checklist items must be
resolved before specialization is treated as validated. No phase gate is
closed by this summary. The leading candidate remains a specialized eFPGA
behind a fixed management shell; capacity and physical evidence must decide
whether it is viable.

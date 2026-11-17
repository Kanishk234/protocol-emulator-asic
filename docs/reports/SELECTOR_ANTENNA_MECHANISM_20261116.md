# Residual antenna investigation — 2026-11-16

Timing closure remains the main objective. Run44025267292 is measuring the
better selector candidate at20ns; no completed extracted result is available.
Antenna is a separate manufacturing gate, now investigated on the same route
rather than preventing all timing measurement.

An antenna violation concerns charge collected by interconnect during wafer
processing that can damage a connected transistor gate. Its name does not mean
the chip contains an RF antenna. Protection depends on the physical layer and
when a diffusion discharge path becomes connected. Diode insertion or a change
in layer routing can help, but must pass the actual technology checker.

## Current measured failure

Retained selector screen43951998125 fresh native antenna report:

| Item | Measurement |
| --- | --- |
| Net / sink | net11655 / _31624_/A2, sg13cmos5l_a21oi_1 |
| Metal2 cumulative ratio / limit | 109.29 / 200 |
| Metal3 cumulative ratio / limit | 252.71 / 200 — failed |
| Metal4 cumulative ratio / limit | 366.18 / 14136 — passed |

These are the retained global-route/checker measurements, not detailed routed
wire lengths. The layer-dependent limit is evidence to inspect actual diffusion
connectivity, not proof that a particular diode is missing or misplaced. Verify
that topology from DRT ODB and repair logs before selecting a local remedy.

The pinned standard-cell LEF has the independently expected SHA256
c47c436758ae87288324aa1f5a84fcc8faf813bf19df1a400b32258fff4e1219.
Its a21oi_1/A2 gate area is0.2418um²; a21oi_2/A2 is0.4836um². Cell areas
are9.072 and14.5152um². At fixed metal geometry and rule accounting, doubling
gate area would halve the reported gate-area ratio; this is a sensitivity
calculation, not a predicted implemented result. Changed input capacitance,
placement, routing, setup and hold all need remeasurement.

There are3111a21oi_1 instances in the retained final netlist. Replacing all
one-for-one would add16933.7952um² of cell area before any flow changes.
Therefore do not globally exclude that cell as a cheap fix for one sink.
Likewise, a fixed-gate geometry would need about20.86% less cumulative numerator
to bring252.71 to200; guide rectangle counts do not measure that numerator.

The pinned technology LEF's Metal2/3/4 cumulative diffusion rules are PWL,
with limit200 below diffusion area0.159um² and increased protection beginning
at0.16um². This is not the constant-diffusion-rule case described in general
OpenROAD diode-repair warnings. Runtime checker topology and loaded technology
must still be inspected. No library/rule edits are made.

Primary files at PDK89d42ee6d2fd9b50b86a1aada6fee6673c3e6008:

- [Standard-cell LEF](https://github.com/IHP-GmbH/IHP-Open-PDK/blob/89d42ee6d2fd9b50b86a1aada6fee6673c3e6008/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lef/sg13cmos5l_stdcell.lef)
- [Technology LEF](https://github.com/IHP-GmbH/IHP-Open-PDK/blob/89d42ee6d2fd9b50b86a1aada6fee6673c3e6008/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lef/sg13cmos5l_tech.lef)

## Action sequence

1. Finish the unchanged native DRT repair/extraction trial already running.
2. Read each repair iteration and the final per-layer antenna report. Identify
   whether the original sink remains, whether new violations appear, and when
   diffusion protection connects; compare actual wires, not global guides.
3. Use actual all-corner extracted paths to choose the next timing change.
   Preserve live configuration timing and native0.25ns uncertainty.
4. If native repair fails, propose a single local routing/protection experiment
   based on that measured topology. Existing D-176 authorizes no manual ECO;
   record any additional experiment scope separately. Do not change a running
   source or wave away its failed check.

This analysis changes no RTL, physical recipe, acceptance gate or claimed phase
status. It prepares a specific fallback while the priority timing run executes.

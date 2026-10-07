# D-047 LUT mapping experiment

This is an isolated CMOS5L LUT4 implementation candidate, not frozen chip RTL.
It preserves all16 runtime configuration bits and uses five actual mux4 cells.
It adds no protocol block or fabric resource.

Hosted37546784325 proves binary combinational equivalence against pinned
FABulous LUTK for every configuration/input and passes2916 partial-input cases
against independent truth-table completion using the actual pinned PDK models.
It does not prove loaded whole-fabric operation, physical area, routing, timing
or sequential initialization.

The native LUT variant workflow copies the authenticated experiment inputs,
applies patches/fabulous_lut_mux_tree.patch to a separate primitive source,
regenerates only native LUT tile netlists with Yosys, and runs the RTL control
and actual mapped candidate UART through real SPI loading. It retains source
hashes, synthesis reports and strict simulation results. Configuration remains
runtime storage; original upstream, generated fabric RTL and frozen chip are
unchanged. Its copied physical views are not qualified for regenerated
netlists. Do not submit those views or promote this candidate without a matched
hardening, physical/timing checks and reproducible real bitstreams.

The original native UART failure remains open independently of any candidate
result. Physical geometry replay and filler experiments use the original saved
database and are independent of this functional mapping experiment.

# Concrete selector source integration review

This prepares the next production review without applying any candidate files.
The bound payload is in `/tmp/tripwire-selector-integration-review-20261116-v2`;
its compact, shareable manifest is `selector_integration_manifest_20261116.json`.
It compares committed baseline e3e51c9 with all170 inputs authenticated against
successful functional regression43946078700, then copies only29 changed files.
Each copied file is checked against the candidate receipt. No Git operations,
production writes or physical tools are part of bundle generation.

The coherent payload includes the actual Tiny Tapeout top and optimized core,
pinned SRAM views/wrapper/PDN inputs, spec and regenerated Verilog/Python tables,
source metadata, test Makefile and actual-top tests. Source-list consistency and
the 8x4/50MHz metadata contract are checked before staging. Existing source
copyright/license headers remain in the copied bytes. Review-only standalone
license, README and eight-view provenance manifest are now prepared in
`docs/review/selector_macro_package/`. All seven text views retain upstream
Apache headers; the exact upstream license is copied without changes. This
package is not applied under macro/ and does not change the active170inputs.

Two adoption decisions remain explicit:

- Current production spec says3lanes/6units; the tested branch floor says
  2lanes/4units. The branch-only decision is not silently turned into approval
  of a new production architecture contract. Finalize resource counts and the
  matching prose contract before applying the bundle.
- The physical recipe changes25 meaningful config fields, plus JSON comment
  metadata, relative to the template baseline. It is the same native recipe
  reviewed November9, not a new tuning change. Several settings lie outside
  the standing production-config whitelist. The earlier exact config review
  remains relevant; publication permission alone does not authorize adoption.

Antenna/timing/congestion, actual detailed route and extraction, final netlist
protocol replay and unchanged official GDS/precheck qualification remain open.
The payload is reviewable evidence, not a qualified release or phase exit.

Reproduce without touching source files:

```sh
source .venv/bin/activate
python scripts/ci/selector_integration_bundle.py \
  --candidate /tmp/tripwire-selector-final-expected-20261116 \
  --regression-archive /tmp/tripwire-selector-43946078700.zip \
  --output /tmp/selector-integration-fresh
```

Use a fresh output directory. The source tree cannot be an output target,
existing payloads are preserved, and any archive/source mismatch is rejected.
The candidate directory is reconstructed by `selector_final_gl.prepare_expected`;
the archive must be the exact whole digest from run43946078700.

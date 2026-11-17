# Integration of the qualified routed candidate

D-184integrates the exact physical inputs from screen44017640255, route/extraction
44031468510 and full22-case replay44123392388. Main source/config, real pinout and
SRAM views match the frozen source byte-for-byte. The2-lane/4-unit/U0-fullspec
retains its existing formatting/comments; its parsed data equals the replay spec.
Generated RTL and Python encodings match the proven physical source/replay tables.
`integration_manifest.json` binds each selected physical input and unchanged
`.github/workflows/gds.yaml`; `verify_integrated_candidate.py` rejects changes.

The project config remains20ns,8x4and stock0.25ns uncertainty. It uses supported
Classic metadata to add native antenna repair after timing, retaining all original
steps. All timing/electrical/antenna/DRC gates remain fixed; this configuration is
an explicit D-184adoption of the previously reviewed policy beyond the old config
whitelist. Official template jobs and action references are not changed.

The counter-placeholder test is replaced by shared UART TX, SPI-controller and
I2C-controller cases on top-level ports. `test/Makefile` supplies committed frozen
SRAM functional models for both RTL and GL. The unchanged official jobs install
test/requirements.txt, which now includes PyYAML for firmware compilation. They do
not install sigrok: reference checks always run, optional decoder checks run where
available, and the separate22-case replay already requires sigrok. No decoder
coverage is inferred from an official environment without the decoder installed.
Macro Apache2license and pinned upstream revision/hash provenance are packaged.

Local checks:
- Generated-file check and top-level Verilator lint pass. Two narrow annotations
  preserve byte-identical RTL: bounded0..23integer comparison, unused intermediate.
- 335Python tests pass with sigrok; initial sandbox runs failed because libusb could
  not initialize. Elevated reruns restore decoder access without changing tests.
- 147core RTL cases pass: fabric7, ALU4, lane6, slots2, owners1, host7,
  lean pin60and full pin60; no skips or failures.
- 3required protocol cases pass through the new template test entry point,
  with reference models and sigrok enabled locally (163.22seconds).
- 32focused integration/provenance/runner tests pass; mutation of a physical input
  is rejected. Input-package audit passes, including macro hashes/licenses.

See `integration_checks.json` for compact evidence. Raw output stays untracked.
The candidate's extracted slow functional setup is+0.163304ns and fast hold
+0.150773287ns; positive reserve remains narrow. This does not guarantee a fresh
hardening. Next is the unchanged official full GDS flow, including remaining
signoff/export checks, precheck, GL and viewer, plus green required main CI.
No Phase2exit box is ticked and no official full-design green is claimed yet.

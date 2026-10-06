# Compiler provenance and image consistency

Local run `uart_fault_provenance_20261005`, 2026-10-05. Successful reports
now include the placement seed, existing control-mapping threshold, strict-port
setting, explicitly listed input SHA-256 hashes and the final image hash.
Listed inputs cover source files, pin map, architecture metadata/pins,
generated FABulous text models, bitstream specification and compiler files.
Recursive includes and vendor binaries/libraries are not fingerprinted.

`python -m compile.audit REPORT` verifies listed files and the image digest,
then checks the bitstream's own CRC, architecture and word count against the
report. It rejects missing files, modified inputs, swapped images, truncated
headers and report/payload disagreement. This is local consistency checking,
not authenticity, functional equivalence, hermetic reproduction or chip timing.
Absolute paths refer to the original build inputs; legacy reports need rebuilding.

Compiler inputs are sampled before port introspection and compared again before
image emission. A detected change rejects the build, with no success image/report.
This is not an atomic filesystem snapshot or protection against deliberate
change-and-restore races.

## Evidence

- Fresh full G1 fault-monitor build and audit PASS:
  `build/uart_fault_provenance_20261005/{report.json,fault.wbit}`;
  `build/uart_fault_provenance_20261005.log`.
- Image is byte-identical to the previously loaded, tested fault-monitor image;
  no new placement or silicon behavior is claimed.
- Actual compiler/Yosys/nextpnr run with an owned source copy deliberately
  changed immediately after placement rejects image emission:
  `build/compiler_input_race_20261005/verification.txt`. Frozen sources untouched.
- Final compiler unit suite51tests PASS27.99s:
  `build/compiler_provenance_all_final_20261005.log`, including nine new
  audit/snapshot cases. Focused14-case provenance/diagnostics suite also passes.

No hardware, host-interface or bitstream-format change. Reproduction uses the
same compile command as the fault-monitor report, with a fresh output directory,
then `python -m compile.audit build/uart_fault_provenance_fresh/report.json`.

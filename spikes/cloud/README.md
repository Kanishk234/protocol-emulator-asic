# Hosted compact experiments

These experiments use standard `ubuntu-24.04` GitHub-hosted runners in this
public repository. No self-hosted/laptop runner, larger runner or paid cloud
service is configured. Public standard runner compute is free under
[GitHub's billing rules](https://docs.github.com/en/billing/concepts/product-billing/github-actions).
Evidence artifacts expire after one day; download important evidence promptly.
Storage has its own limits and is not claimed to be unlimited.

`experiments.yaml` runs three independent jobs:

- Resume the saved compact route, with a 300-minute step limit, four threads
  and the stock antenna/DRC/disconnected-pin checks. Only zero native failures
  permit extraction, shell STA and the remaining stock physical checks.
- Load the UART image through real SPI on the tighter RTL fabric control and
  then its actual mapped fabric. Native failures stay failures.
- Freshly compile/audit and SPI-load four G1 monitor/fault/capture demos on RTL.

The native job uses the existing D-023 routing-settling harness, not forced
configuration or user storage. These tests contain no SDF. Shell STA black-boxes
the fabric macro, so success does not close configured-fabric timing.

The 5.41 MiB checkpoint is a separately published experimental prerelease asset,
not a binary committed to Git. `checkpoint.json` pins its whole-archive SHA256;
the embedded manifest also hashes every input and binds the 15-marker iteration8
ODB. Extraction rejects path traversal, links and devices. Inputs materialize
under a fresh ignored `build/cloud_input/` directory. This is checkpoint
reproduction, **not** the still-needed clean-source fabric rebuild.

The host flow uses LibreLane3.1.0.dev3 Docker, the exact PDK revision in the
manifest and OpenROAD source revision dcf36133. Relative to the local preserved
run, LibreLane packaging and thread count change: do not attribute differences
solely to the iteration limit. Frozen G1 hardware and template workflows remain
unchanged. Keep each subsequent physical change isolated.

Pushes changing `spikes/cloud/` or this workflow on `efpga` start the jobs.
Manual dispatch requires a workflow on the default branch; `main` is the
separate TRIPWIRE project and is left untouched. Rerun an existing experiment
with `gh run rerun RUN_ID`, or push reviewed experiment changes on `efpga`.
`collect.py` retains reports, metrics, logs and one last completed ODB, avoiding
dozens of redundant databases. An intermediate marker count is never a pass.

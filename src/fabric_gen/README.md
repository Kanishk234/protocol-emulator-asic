# Generated integration prototype

FABulous-FPGA 2.2.0 stock template, generated using the small grid recorded
in `arch/small_reference.csv`. Original Apache-2.0 license/copyright headers
are preserved in the supplied primitive files; see the repository LICENSE.

Reproduce from the cached compile with the project venv:
`python scripts/integrate_small_fabric.py build/warp-small-compile.khvqjtBG`.
The compile itself is reproduced with `scripts/fabric_small_compile.sh`.
`manifest.json` records original and transformed source SHA-256 values.
The checked transformation propagates LUT/carry hold through two tiles and
selects the word-only ConfigFSM path. It preserves dynamic configuration.

Do not manually edit these files. This is an experimental reference-derived
integration, not the frozen protocol fabric or a physical signoff result.

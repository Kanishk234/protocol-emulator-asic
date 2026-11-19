# Next configured timing investigation

The original native timing control remains unqualified: six endpoints differ
between static and dynamic loop handling, despite +1.508933 ns cell-only worst
setup slack. Unused G output-register, D input-selector and E input-selector
experiments all leave endpoint values unchanged. None is adopted or combined.

The actual original eight-loop report names 23 native cells around X2Y3 and
X2Y4. D133 queries all 70 input/output pin pairs and their cell pin constants
using the already tested pinned OpenSTA report APIs. It runs the two unchanged
controls, with reports appended after original measurements. Coverage and input
hashes must pass, and the original six sensitive endpoints must reproduce.
The result grants no timing acceptance and adds no timing exception.

[Current upstream Levelize.cc](https://github.com/The-OpenROAD-Project/OpenSTA/blob/master/search/Levelize.cc)
uses a structural traversal predicate which does not visibly test the
constant-simulation disabled flag. This suggests investigating whether structural
cuts can affect selected paths despite case-disabled edges. That is an inference
from current upstream code, **not a verified diagnosis of the pinned 2.7 binary**.
The pinned implementation must be checked before any tool patch or model change;
newer upstream command flags are not assumed compatible.

All 26 leaves now have individual physical finishing passes. This supplies
routed/extracted leaf views for subsequent work, but it does not establish
assembled fabric, clock distribution, shell integration or configured timing.
The assembly catalog allocates distinct physical masters before stitching;
full-macro geometry/LVS and matched extracted timing still need real runs.

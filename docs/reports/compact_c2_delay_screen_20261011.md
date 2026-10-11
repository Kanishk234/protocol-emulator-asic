# Generic C2 user-register delay: intrinsic result and physical trial

Actual38113263802 completes twelve cases on47d7b33. Exact libraries match
precise extracted reference38112173902; both compared variants deliberately
omit parasitics. Two loaded UART positions, three original PVT libraries,
same20ns clock/margins, same529 stationary configuration values per position
and eight dynamic user FF states. Root verified all report hashes and native
path summaries. This is Liberty-only screening, not extracted timing.

| Position | Fast baseline hold ns | Fast delay hold ns | Fast hold violations baseline→delay | Slow baseline setup ns | Slow delay setup ns |
|---|---:|---:|---:|---:|---:|
| X2Y1 |−0.049636|0.035163|6→0|16.940542|16.711065|
| X2Y3 |−0.061607|0.022388|2→0|16.687424|16.457949|

All six delay cases retain positive examined setup/hold with zero native
violation labels. Their path counts match baseline28/26 per mode at each
position. Non-inverting dlygate4sd1_1 is inserted at every user D pin; removing
the eight identities reproduces the exact original source. No configuration
bit, user register, pin interface, state case, false path or clock margin changes.

The actual library catalogue records14.5152µm² per delay cell in this run.
Eight cells imply116.1216µm² of catalogue cell area, excluding legalization,
wires, repairs and power cost. This is not measured routed chip area. Every
design pays data delay and physical space even without the observed failure.
Result SHA c2955785c0c3e1820a1500f4a1b50830e5da2751d974666a75c048df91639ef5;
copied final-NL screen SHA27c763601a92e9edc107ba470dc4cf511481b1deac458b18407de52e05ad3237.

The next trial derives the same eight identities from the authenticated
pre-buffer mapped source03c21b8e…, not the final netlist. This avoids adding the
original output adapters twice. Reuse the original no-synthesis hardening
sequence, original interfaces/footprint/PG/routing policy, real antenna,
disconnected, Magic/KLayout and LVS checks. Pre-buffer candidate SHA
842dae88a1dec2a8579e63df7db953d7f9c6a54752df2a2b886a328ed74053e2.
Original virtual-clock timing errors remain visible; physical collection
cannot qualify configured timing. New actual extracted and loaded-function
checks are required after a physical candidate exists. Other tile types and
full intertile/shell timing remain open; no protocol-rate or all-image claim.
